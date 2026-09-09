package handler

import (
	"context"
	"encoding/json"
	"errors"
	"net/http"
	"time"

	"github.com/luizcaixeta/painel_sigesguarda/api/internal/services"
)

type BairrosGeoJSONHandler struct {
	lister  BairroLister
	timeout time.Duration
}

type bairroFeatureCollection struct {
	Type     string          `json:"type"`
	Features []bairroFeature `json:"features"`
}

type bairroFeature struct {
	Type       string          `json:"type"`
	Properties bairroResponse  `json:"properties"`
	Geometry   json.RawMessage `json:"geometry"`
}

func NewBairrosGeoJSONHandler(lister BairroLister, timeout time.Duration) *BairrosGeoJSONHandler {
	return &BairrosGeoJSONHandler{
		lister:  lister,
		timeout: timeout,
	}
}

func (handler *BairrosGeoJSONHandler) ServeHTTP(w http.ResponseWriter, r *http.Request) {
	if len(r.URL.Query()) != 0 {
		WriteError(
			w,
			r,
			http.StatusBadRequest,
			"INVALID_ARGUMENT",
			"invalid query parameter",
		)
		return
	}

	ctx, cancel := context.WithTimeout(r.Context(), handler.timeout)
	defer cancel()

	bairros, err := handler.lister.ListBairrosGeoJSON(ctx)
	if err != nil {
		if errors.Is(err, services.ErrDataNotReady) {
			WriteError(
				w,
				r,
				http.StatusServiceUnavailable,
				"DATA_NOT_READY",
				"bairro geometry catalog unavailable",
			)
			return
		}

		WriteError(
			w,
			r,
			http.StatusServiceUnavailable,
			"DATABASE_UNAVAILABLE",
			"database unavailable",
		)
		return
	}

	features := make([]bairroFeature, len(bairros))
	for index, bairro := range bairros {
		features[index] = bairroFeature{
			Type: "Feature",
			Properties: bairroResponse{
				BairroID: bairro.ID,
				Nome:     bairro.Nome,
			},
			Geometry: bairro.Geometry,
		}
	}

	WriteGeoJSON(w, http.StatusOK, bairroFeatureCollection{
		Type:     "FeatureCollection",
		Features: features,
	})
}
