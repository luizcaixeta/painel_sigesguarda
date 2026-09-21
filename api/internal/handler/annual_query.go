package handler

import (
	"fmt"
	"net/url"
	"strconv"

	"github.com/luizcaixeta/painel_sigesguarda/api/internal/domain"
)

const (
	minimumAnnualYear = 2009
	maximumAnnualYear = 2050
)

func parseAnnualFilter(query url.Values) (domain.AnnualFilter, error) {
	bairroIDs, err := parseUniqueValues(query, "bairro_id", 75)
	if err != nil {
		return domain.AnnualFilter{}, err
	}
	for _, bairroID := range bairroIDs {
		if len(bairroID) > 100 {
			return domain.AnnualFilter{}, fmt.Errorf("invalid bairro_id")
		}
	}

	yearValues, err := parseUniqueValues(
		query,
		"ano",
		maximumAnnualYear-minimumAnnualYear+1,
	)
	if err != nil {
		return domain.AnnualFilter{}, err
	}
	years := make([]int32, len(yearValues))
	for index, value := range yearValues {
		years[index], err = parseYear(value)
		if err != nil {
			return domain.AnnualFilter{}, err
		}
	}

	de, hasDe, err := parseOptionalYear(query, "de")
	if err != nil {
		return domain.AnnualFilter{}, err
	}
	ate, hasAte, err := parseOptionalYear(query, "ate")
	if err != nil {
		return domain.AnnualFilter{}, err
	}

	if len(years) > 0 && (hasDe || hasAte) {
		return domain.AnnualFilter{}, fmt.Errorf("ano cannot be combined with de or ate")
	}
	if hasDe != hasAte {
		return domain.AnnualFilter{}, fmt.Errorf("de and ate must be provided together")
	}
	if hasDe && de > ate {
		return domain.AnnualFilter{}, fmt.Errorf("de cannot be after ate")
	}

	filter := domain.AnnualFilter{BairroIDs: bairroIDs, Anos: years}
	if hasDe {
		filter.De = &de
		filter.Ate = &ate
	}
	return filter, nil
}

func parseOptionalYear(query url.Values, name string) (int32, bool, error) {
	values, exists := query[name]
	if !exists {
		return 0, false, nil
	}
	if len(values) != 1 || values[0] == "" {
		return 0, false, fmt.Errorf("invalid value for %s", name)
	}
	year, err := parseYear(values[0])
	return year, true, err
}

func parseYear(value string) (int32, error) {
	year, err := strconv.ParseInt(value, 10, 32)
	if err != nil || year < minimumAnnualYear || year > maximumAnnualYear {
		return 0, fmt.Errorf("invalid year %q", value)
	}
	return int32(year), nil
}
