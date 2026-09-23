package errs

import (
	"errors"
	"net/http"
)

type Kind uint8

const (
	KindInternal Kind = iota
	KindInvalidArgument
	KindInvalidBairroFilter
	KindInvalidCategoriaFilter
	KindInvalidIndicadorFilter
	KindRouteNotFound
	KindMethodNotAllowed
	KindDataContractNotReady
	KindBairroCatalogNotReady
	KindBairroGeometryCatalogNotReady
	KindCategoriaCatalogNotReady
	KindIndicadorCatalogNotReady
	KindCurrentGoldBatchNotReady
	KindCurrentSocioeconomicGoldBatchNotReady
	KindForecastNotReady
	KindDatabaseUnavailable
)

type Code string

const (
	CodeInvalidArgument     Code = "INVALID_ARGUMENT"
	CodeInvalidFilter       Code = "INVALID_FILTER"
	CodeNotFound            Code = "NOT_FOUND"
	CodeMethodNotAllowed    Code = "METHOD_NOT_ALLOWED"
	CodeDataNotReady        Code = "DATA_NOT_READY"
	CodeForecastNotReady    Code = "FORECAST_NOT_READY"
	CodeDatabaseUnavailable Code = "DATABASE_UNAVAILABLE"
	CodeInternalError       Code = "INTERNAL_ERROR"
)

type HTTPDefinition struct {
	Status  int
	Code    Code
	Message string
}

type applicationError struct {
	kind      Kind
	operation string
	cause     error
}

func New(kind Kind) error {
	return &applicationError{kind: kind}
}

func Wrap(kind Kind, operation string, cause error) error {
	if cause == nil {
		return nil
	}

	return &applicationError{
		kind:      kind,
		operation: operation,
		cause:     cause,
	}
}

func (err *applicationError) Error() string {
	switch {
	case err.operation != "" && err.cause != nil:
		return err.operation + ": " + err.cause.Error()
	case err.cause != nil:
		return err.cause.Error()
	case err.operation != "":
		return err.operation
	default:
		return HTTPDefinitionFor(err.kind).Message
	}
}

func (err *applicationError) Unwrap() error {
	return err.cause
}

func KindOf(err error) (Kind, bool) {
	var classified *applicationError
	if errors.As(err, &classified) {
		return classified.kind, true
	}
	return KindInternal, false
}

func IsKind(err error, kind Kind) bool {
	classifiedKind, classified := KindOf(err)
	return classified && classifiedKind == kind
}

func Resolve(err error) HTTPDefinition {
	kind, classified := KindOf(err)
	if !classified {
		kind = KindInternal
	}
	return HTTPDefinitionFor(kind)
}

func HTTPDefinitionFor(kind Kind) HTTPDefinition {
	switch kind {
	case KindInvalidArgument:
		return HTTPDefinition{
			Status:  http.StatusBadRequest,
			Code:    CodeInvalidArgument,
			Message: "invalid query parameter",
		}
	case KindInvalidBairroFilter:
		return HTTPDefinition{
			Status:  http.StatusBadRequest,
			Code:    CodeInvalidFilter,
			Message: "unknown bairro_id",
		}
	case KindInvalidCategoriaFilter:
		return HTTPDefinition{
			Status:  http.StatusBadRequest,
			Code:    CodeInvalidFilter,
			Message: "unknown categoria",
		}
	case KindInvalidIndicadorFilter:
		return HTTPDefinition{
			Status:  http.StatusBadRequest,
			Code:    CodeInvalidFilter,
			Message: "unknown indicador",
		}
	case KindRouteNotFound:
		return HTTPDefinition{
			Status:  http.StatusNotFound,
			Code:    CodeNotFound,
			Message: "route not found",
		}
	case KindMethodNotAllowed:
		return HTTPDefinition{
			Status:  http.StatusMethodNotAllowed,
			Code:    CodeMethodNotAllowed,
			Message: "method not allowed",
		}
	case KindDataContractNotReady:
		return HTTPDefinition{
			Status:  http.StatusServiceUnavailable,
			Code:    CodeDataNotReady,
			Message: "data contract unavailable",
		}
	case KindBairroCatalogNotReady:
		return HTTPDefinition{
			Status:  http.StatusServiceUnavailable,
			Code:    CodeDataNotReady,
			Message: "bairro catalog unavailable",
		}
	case KindBairroGeometryCatalogNotReady:
		return HTTPDefinition{
			Status:  http.StatusServiceUnavailable,
			Code:    CodeDataNotReady,
			Message: "bairro geometry catalog unavailable",
		}
	case KindCategoriaCatalogNotReady:
		return HTTPDefinition{
			Status:  http.StatusServiceUnavailable,
			Code:    CodeDataNotReady,
			Message: "categoria catalog unavailable",
		}
	case KindIndicadorCatalogNotReady:
		return HTTPDefinition{
			Status:  http.StatusServiceUnavailable,
			Code:    CodeDataNotReady,
			Message: "indicador catalog unavailable",
		}
	case KindCurrentGoldBatchNotReady:
		return HTTPDefinition{
			Status:  http.StatusServiceUnavailable,
			Code:    CodeDataNotReady,
			Message: "current Gold batch unavailable",
		}
	case KindCurrentSocioeconomicGoldBatchNotReady:
		return HTTPDefinition{
			Status:  http.StatusServiceUnavailable,
			Code:    CodeDataNotReady,
			Message: "current socioeconomic Gold batch unavailable",
		}
	case KindForecastNotReady:
		return HTTPDefinition{
			Status:  http.StatusServiceUnavailable,
			Code:    CodeForecastNotReady,
			Message: "compatible complete forecast unavailable",
		}
	case KindDatabaseUnavailable:
		return HTTPDefinition{
			Status:  http.StatusServiceUnavailable,
			Code:    CodeDatabaseUnavailable,
			Message: "database unavailable",
		}
	default:
		return HTTPDefinition{
			Status:  http.StatusInternalServerError,
			Code:    CodeInternalError,
			Message: "internal server error",
		}
	}
}
