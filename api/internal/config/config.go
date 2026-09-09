package config

import (
	"fmt"
	"os"
	"time"
)

type Config struct {
	APIAddr           string
	ReadHeaderTimeout time.Duration
	ReadTimeout       time.Duration
	WriteTimeout      time.Duration
	IdleTimeout       time.Duration
	ShutdownTimeout   time.Duration
}

func parseString(name string) (string, error) {
	rawValue := os.Getenv(name)
	if rawValue == "" {
		return "", fmt.Errorf("the environment variable %s was not defined", name)
	}

	return rawValue, nil
}

func parseDuration(name string) (time.Duration, error) {
	rawValue := os.Getenv(name)
	if rawValue == "" {
		return 0, fmt.Errorf("the environment variable %s was not defined", name)
	}

	duration, err := time.ParseDuration(rawValue)
	if err != nil {
		return 0, fmt.Errorf("error converting %s: %w", name, err)
	}

	if duration <= 0 {
		return 0, fmt.Errorf("the timeout %s must be positive", name)
	}

	return duration, nil
}

func Load() (Config, error) {
	var cfg Config
	var err error

	cfg.APIAddr, err = parseString("API_SIGESGUARDA_ADDR")
	if err != nil {
		return Config{}, err
	}

	cfg.ReadHeaderTimeout, err = parseDuration("API_SIGESGUARDA_READ_HEADER_TIMEOUT")
	if err != nil {
		return Config{}, err
	}

	cfg.ReadTimeout, err = parseDuration("API_SIGESGUARDA_READ_TIMEOUT")
	if err != nil {
		return Config{}, err
	}

	cfg.WriteTimeout, err = parseDuration("API_SIGESGUARDA_WRITE_TIMEOUT")
	if err != nil {
		return Config{}, err
	}

	cfg.IdleTimeout, err = parseDuration("API_SIGESGUARDA_IDLE_TIMEOUT")
	if err != nil {
		return Config{}, err
	}

	cfg.ShutdownTimeout, err = parseDuration("API_SIGESGUARDA_SHUTDOWN_TIMEOUT")
	if err != nil {
		return Config{}, err
	}

	return cfg, nil
}
