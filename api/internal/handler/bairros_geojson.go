package handler

import (
	"context"
	"encoding/json"
	"net/http"
	"time"

	"github.com/luizcaixeta/painel_sigesguarda/api/internal/errs"
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
		WriteError(w, r, errs.New(errs.KindInvalidArgument))
		return
	}

	ctx, cancel := context.WithTimeout(r.Context(), handler.timeout)
	defer cancel()

	bairros, err := handler.lister.ListBairrosGeoJSON(ctx)
	if err != nil {
		WriteError(w, r, err)
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
