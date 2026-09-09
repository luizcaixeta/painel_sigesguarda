package config

import (
	"fmt"
	"net"
	"net/url"
	"os"
	"strconv"
	"time"
)

type Config struct {
	APIAddr           string
	ReadHeaderTimeout time.Duration
	ReadTimeout       time.Duration
	WriteTimeout      time.Duration
	IdleTimeout       time.Duration
	ShutdownTimeout   time.Duration
	DatabaseDSN       string
	DBMaxConns        int32
	DBMinConns        int32
	QueryTimeout      time.Duration
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

func parseInt32(name string) (int32, error) {
	rawValue := os.Getenv(name)
	if rawValue == "" {
		return 0, fmt.Errorf("the environment variable %s was not defined", name)
	}

	value, err := strconv.ParseInt(rawValue, 10, 32)
	if err != nil {
		return 0, fmt.Errorf("error converting %s: %w", name, err)
	}

	return int32(value), nil
}

func buildDatabaseDSN() (string, error) {
	host, err := parseString("SIGESGUARDA_DATABASE.HOST")
	if err != nil {
		return "", err
	}

	port, err := parseString("SIGESGUARDA_DATABASE.PORT")
	if err != nil {
		return "", err
	}

	user, err := parseString("SIGESGUARDA_DATABASE.USER")
	if err != nil {
		return "", err
	}

	password, err := parseString("SIGESGUARDA_DATABASE.PASSWORD")
	if err != nil {
		return "", err
	}

	name, err := parseString("SIGESGUARDA_DATABASE.NAME")
	if err != nil {
		return "", err
	}

	sslMode, err := parseString("SIGESGUARDA_DATABASE.SSL_MODE")
	if err != nil {
		return "", err
	}

	databaseURL := &url.URL{
		Scheme: "postgres",
		User:   url.UserPassword(user, password),
		Host:   net.JoinHostPort(host, port),
		Path:   name,
	}
	query := databaseURL.Query()
	query.Set("sslmode", sslMode)
	databaseURL.RawQuery = query.Encode()

	return databaseURL.String(), nil
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

	cfg.DatabaseDSN, err = buildDatabaseDSN()
	if err != nil {
		return Config{}, err
	}

	cfg.DBMaxConns, err = parseInt32("API_SIGESGUARDA_DB_MAX_CONNS")
	if err != nil {
		return Config{}, err
	}

	cfg.DBMinConns, err = parseInt32("API_SIGESGUARDA_DB_MIN_CONNS")
	if err != nil {
		return Config{}, err
	}

	cfg.QueryTimeout, err = parseDuration("API_SIGESGUARDA_QUERY_TIMEOUT")
	if err != nil {
		return Config{}, err
	}

	if cfg.DBMaxConns <= 0 {
		return Config{}, fmt.Errorf("API_SIGESGUARDA_DB_MAX_CONNS must be positive")
	}

	if cfg.DBMinConns < 0 {
		return Config{}, fmt.Errorf("API_SIGESGUARDA_DB_MIN_CONNS cannot be negative")
	}

	if cfg.DBMinConns > cfg.DBMaxConns {
		return Config{}, fmt.Errorf("API_SIGESGUARDA_DB_MIN_CONNS cannot exceed API_SIGESGUARDA_DB_MAX_CONNS")
	}

	return cfg, nil
}
