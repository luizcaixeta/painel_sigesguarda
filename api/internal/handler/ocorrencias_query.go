package handler

import (
	"fmt"
	"net/url"
	"time"

	"github.com/luizcaixeta/painel_sigesguarda/api/internal/domain"
)

var ocorrenciasQueryParameters = map[string]struct{}{
	"bairro_id": {},
	"categoria": {},
	"mes":       {},
	"de":        {},
	"ate":       {},
}

func parseOcorrenciasQuery(query url.Values) (domain.OcorrenciasFilter, error) {
	for name := range query {
		if _, allowed := ocorrenciasQueryParameters[name]; !allowed {
			return domain.OcorrenciasFilter{}, fmt.Errorf(
				"unknown query parameter %q",
				name,
			)
		}
	}

	bairroIDs, err := parseUniqueValues(query, "bairro_id", 75)
	if err != nil {
		return domain.OcorrenciasFilter{}, err
	}
	for _, bairroID := range bairroIDs {
		if len(bairroID) > 100 {
			return domain.OcorrenciasFilter{}, fmt.Errorf("invalid bairro_id")
		}
	}

	categorias, err := parseUniqueValues(query, "categoria", 6)
	if err != nil {
		return domain.OcorrenciasFilter{}, err
	}

	monthValues, err := parseUniqueValues(query, "mes", 240)
	if err != nil {
		return domain.OcorrenciasFilter{}, err
	}

	meses := make([]time.Time, len(monthValues))
	for index, value := range monthValues {
		meses[index], err = parseMonth(value)
		if err != nil {
			return domain.OcorrenciasFilter{}, err
		}
	}

	de, hasDe, err := parseOptionalMonth(query, "de")
	if err != nil {
		return domain.OcorrenciasFilter{}, err
	}

	ate, hasAte, err := parseOptionalMonth(query, "ate")
	if err != nil {
		return domain.OcorrenciasFilter{}, err
	}

	if len(meses) > 0 && (hasDe || hasAte) {
		return domain.OcorrenciasFilter{}, fmt.Errorf(
			"mes cannot be combined with de or ate",
		)
	}

	if hasDe != hasAte {
		return domain.OcorrenciasFilter{}, fmt.Errorf(
			"de and ate must be provided together",
		)
	}

	if hasDe && de.After(ate) {
		return domain.OcorrenciasFilter{}, fmt.Errorf("de cannot be after ate")
	}

	if hasDe && inclusiveMonthCount(de, ate) > 240 {
		return domain.OcorrenciasFilter{}, fmt.Errorf(
			"month range cannot exceed 240 months",
		)
	}

	filter := domain.OcorrenciasFilter{
		BairroIDs:  bairroIDs,
		Categorias: categorias,
		Meses:      meses,
	}
	if hasDe {
		filter.De = &de
		filter.Ate = &ate
	}

	return filter, nil
}

func parseUniqueValues(query url.Values, name string, maximum int) ([]string, error) {
	values, exists := query[name]
	if !exists {
		return nil, nil
	}

	if len(values) == 0 || len(values) > maximum {
		return nil, fmt.Errorf("invalid number of values for %s", name)
	}

	seen := make(map[string]struct{}, len(values))
	for _, value := range values {
		if value == "" {
			return nil, fmt.Errorf("empty value for %s", name)
		}
		if _, duplicated := seen[value]; duplicated {
			return nil, fmt.Errorf("duplicated value for %s", name)
		}
		seen[value] = struct{}{}
	}

	return values, nil
}

func parseOptionalMonth(query url.Values, name string) (time.Time, bool, error) {
	values, exists := query[name]
	if !exists {
		return time.Time{}, false, nil
	}

	if len(values) != 1 || values[0] == "" {
		return time.Time{}, false, fmt.Errorf("invalid value for %s", name)
	}

	month, err := parseMonth(values[0])
	if err != nil {
		return time.Time{}, false, err
	}

	return month, true, nil
}

func parseMonth(value string) (time.Time, error) {
	if len(value) != len("2006-01") {
		return time.Time{}, fmt.Errorf("invalid month %q", value)
	}

	month, err := time.Parse("2006-01", value)
	if err != nil {
		return time.Time{}, fmt.Errorf("invalid month %q: %w", value, err)
	}

	return month, nil
}

func inclusiveMonthCount(start time.Time, end time.Time) int {
	return (end.Year()-start.Year())*12 + int(end.Month()-start.Month()) + 1
}
