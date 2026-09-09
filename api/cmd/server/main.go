package main

import (
	"context"
	"errors"
	"fmt"
	"log/slog"
	"net/http"
	"os"
	"os/signal"
	"syscall"

	"github.com/joho/godotenv"
	"github.com/luizcaixeta/painel_sigesguarda/api/internal/config"
	"github.com/luizcaixeta/painel_sigesguarda/api/internal/database"
	"github.com/luizcaixeta/painel_sigesguarda/api/internal/repositories"
	"github.com/luizcaixeta/painel_sigesguarda/api/internal/router"
	"github.com/luizcaixeta/painel_sigesguarda/api/internal/services"
)

func run() error {
	if err := godotenv.Load(); err != nil && !errors.Is(err, os.ErrNotExist) {
		return fmt.Errorf("load .env: %w", err)
	}

	cfg, err := config.Load()
	if err != nil {
		return fmt.Errorf("load configuration: %w", err)
	}

	databaseContext, cancelDatabase := context.WithTimeout(
		context.Background(),
		cfg.QueryTimeout,
	)
	pool, err := database.NewPool(
		databaseContext,
		cfg.DatabaseDSN,
		cfg.DBMinConns,
		cfg.DBMaxConns,
	)
	cancelDatabase()
	if err != nil {
		return fmt.Errorf("initialize database: %w", err)
	}
	defer pool.Close()

	readinessChecker := database.NewReadinessChecker(pool)
	bairroRepository := repositories.NewBairroRepository(pool)
	bairroService := services.NewBairroService(bairroRepository)
	httpHandler := router.New(readinessChecker, bairroService, cfg.QueryTimeout)

	server := &http.Server{
		Addr:              cfg.APIAddr,
		Handler:           httpHandler,
		ReadHeaderTimeout: cfg.ReadHeaderTimeout,
		ReadTimeout:       cfg.ReadTimeout,
		WriteTimeout:      cfg.WriteTimeout,
		IdleTimeout:       cfg.IdleTimeout,
	}

	shutdownSignal, stop := signal.NotifyContext(
		context.Background(),
		os.Interrupt,
		syscall.SIGTERM,
	)
	defer stop()

	serverErrors := make(chan error, 1)
	go func() {
		slog.Info("HTTP server starting", "address", cfg.APIAddr)
		serverErrors <- server.ListenAndServe()
	}()

	select {
	case err = <-serverErrors:
		if err != nil && !errors.Is(err, http.ErrServerClosed) {
			return fmt.Errorf("serve HTTP: %w", err)
		}
		return nil
	case <-shutdownSignal.Done():
		stop()
		slog.Info("shutdown signal received")
	}

	shutdownContext, cancelShutdown := context.WithTimeout(
		context.Background(),
		cfg.ShutdownTimeout,
	)
	defer cancelShutdown()

	if err = server.Shutdown(shutdownContext); err != nil {
		_ = server.Close()
		return fmt.Errorf("shutdown HTTP server: %w", err)
	}

	if err = <-serverErrors; err != nil && !errors.Is(err, http.ErrServerClosed) {
		return fmt.Errorf("serve HTTP during shutdown: %w", err)
	}

	slog.Info("HTTP server stopped")
	return nil
}

func main() {
	if err := run(); err != nil {
		slog.Error("application stopped", "error", err)
		os.Exit(1)
	}
}
