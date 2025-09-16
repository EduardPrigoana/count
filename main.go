package main

import (
	"context"
	"encoding/json"
	"log"
	"net/http"
	"os"
	"os/signal"
	"regexp"
	"strings"
	"syscall"
	"time"

	"github.com/joho/godotenv"
	"github.com/redis/go-redis/v9"
)

const (
	maxKeyLength          = 1024
	serverShutdownTimeout = 5 * time.Second
)

var (
	redisClient    *redis.Client
	forbiddenExact = map[string]struct{}{
		".env": {}, "config.json": {}, "config.yaml": {}, "settings.php": {}, "credentials.json": {},
		"secrets.json": {}, "docker-compose.yml": {}, "backup.zip": {}, "database.sql": {}, "info.php": {},
		"phpinfo.php": {}, "debug.log": {}, "admin": {}, "administrator": {}, "wp-login.php": {}, "phpmyadmin": {},
		"install.php": {}, "swagger-ui.html": {}, "api-docs": {}, "server-status": {},
	}
	forbiddenPrefixes = []string{".", "docker-", "wp-", "wordpress/", "administrator/", "admin/", "phpmyadmin/", "actuator/", "api/", "v1/", "v2/", "backup/", "temp/", "tmp/"}
	keyValidator      = regexp.MustCompile(`^[A-Za-z0-9._:-]+$`)
)

func jsonError(w http.ResponseWriter, message string, code int) {
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(code)
	_ = json.NewEncoder(w).Encode(map[string]string{"error": message})
}

func corsMiddleware(next http.Handler, allowedOrigin string) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		w.Header().Set("Access-Control-Allow-Origin", allowedOrigin)
		w.Header().Set("Access-Control-Allow-Methods", "GET, OPTIONS")
		w.Header().Set("Access-Control-Allow-Headers", "Accept, Content-Type, Content-Length, Accept-Encoding")
		if r.Method == http.MethodOptions {
			w.WriteHeader(http.StatusNoContent)
			return
		}
		next.ServeHTTP(w, r)
	})
}

func securityMiddleware(next http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		orig := r.URL.Path
		if orig == "./" || strings.HasPrefix(orig, "/./") || orig == "." {
			http.Redirect(w, r, "https://prigoana.com", http.StatusFound)
			return
		}
		p := strings.Trim(orig, "/")
		if _, ok := forbiddenExact[p]; ok {
			http.Redirect(w, r, "https://prigoana.com", http.StatusFound)
			return
		}
		for _, prefix := range forbiddenPrefixes {
			if strings.HasPrefix(p, prefix) {
				http.Redirect(w, r, "https://prigoana.com", http.StatusFound)
				return
			}
		}
		next.ServeHTTP(w, r)
	})
}

func countHandler(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodGet {
		jsonError(w, "Method not allowed", http.StatusMethodNotAllowed)
		return
	}
	if r.URL.Path == "/" {
		w.Header().Set("Content-Type", "text/plain")
		w.WriteHeader(http.StatusOK)
		_, _ = w.Write([]byte("1"))
		return
	}
	if r.URL.Path == "/favicon.ico" {
		w.WriteHeader(http.StatusNoContent)
		return
	}
	key := strings.Trim(r.URL.Path, "/")
	if len(key) == 0 || len(key) > maxKeyLength {
		jsonError(w, "Key is invalid or too long", http.StatusBadRequest)
		return
	}
	key = strings.ReplaceAll(key, "/", ":")
	if !keyValidator.MatchString(key) {
		jsonError(w, "Key contains invalid characters", http.StatusBadRequest)
		return
	}
	ctx, cancel := context.WithTimeout(r.Context(), 3*time.Second)
	defer cancel()
	count, err := redisClient.Incr(ctx, key).Result()
	if err != nil {
		if err == context.Canceled || err == context.DeadlineExceeded {
			jsonError(w, "Request timed out", http.StatusGatewayTimeout)
			return
		}
		log.Printf("redis error: %v", err)
		jsonError(w, "Service is temporarily unavailable", http.StatusServiceUnavailable)
		return
	}
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(http.StatusOK)
	_ = json.NewEncoder(w).Encode(map[string]int64{"count": count})
}

func main() {
	_ = godotenv.Load()
	redisURL := os.Getenv("REDIS_URL")
	if redisURL == "" {
		log.Fatal("REDIS_URL not set")
	}
	port := os.Getenv("PORT")
	if port == "" {
		port = "5000"
	}
	corsOrigin := os.Getenv("CORS_ALLOWED_ORIGIN")
	if corsOrigin == "" {
		corsOrigin = "*"
	}
	opt, err := redis.ParseURL(redisURL)
	if err != nil {
		log.Fatalf("invalid redis url: %v", err)
	}
	redisClient = redis.NewClient(opt)
	ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
	defer cancel()
	if err := redisClient.Ping(ctx).Err(); err != nil {
		log.Fatalf("cannot reach redis: %v", err)
	}
	defer func() {
		_ = redisClient.Close()
	}()
	mux := http.NewServeMux()
	mux.HandleFunc("/", countHandler)
	handler := corsMiddleware(securityMiddleware(mux), corsOrigin)
	server := &http.Server{
		Addr:         ":" + port,
		Handler:      handler,
		ReadTimeout:  5 * time.Second,
		WriteTimeout: 10 * time.Second,
		IdleTimeout:  120 * time.Second,
	}
	stop := make(chan os.Signal, 1)
	signal.Notify(stop, syscall.SIGINT, syscall.SIGTERM)
	go func() {
		if err := server.ListenAndServe(); err != nil && err != http.ErrServerClosed {
			log.Fatalf("server error: %v", err)
		}
	}()
	<-stop
	ctxShutdown, cancelShutdown := context.WithTimeout(context.Background(), serverShutdownTimeout)
	defer cancelShutdown()
	if err := server.Shutdown(ctxShutdown); err != nil {
		log.Printf("graceful shutdown failed: %v", err)
	}
}
