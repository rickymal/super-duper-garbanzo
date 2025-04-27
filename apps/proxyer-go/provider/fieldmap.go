package provider

import (
	"database/sql"
	"errors"
	"reflect"
	"regexp"
	"strings"
)

// FieldMap é um map especial que também fornece pares (cols, vals)
// prontos para builders de INSERT/UPDATE.
// Exemplo de uso:
//   fm, _ := MakeFieldMapFromStruct(user)
//   cols, vals := fm.ToPair()
//   sess.InsertInto("users").Columns(cols...).Values(vals...).Exec()
//
//  - Converte nomes CamelCase em snake_case
//  - Ignora campos sql.NullString (ou sentinel) não válidos
//  - Ignora campos zero/nil
//  - Apenas campos exportados
//
// Obs.: Pode ser estendido para lidar com outros sentinelas implementando IsZero().

type FieldMap map[string]any

// ToPair devolve duas slices paralelas: colunas e valores.
func (fm FieldMap) ToPair() ([]string, []any) {
	cols := make([]string, 0, len(fm))
	vals := make([]any, 0, len(fm))
	for k, v := range fm {
		cols = append(cols, k)
		vals = append(vals, v)
	}
	return cols, vals
}

var camelRegexp = regexp.MustCompile(`([a-z0-9])([A-Z])`)

func camelToSnake(s string) string {
	snake := camelRegexp.ReplaceAllString(s, "${1}_${2}")
	return strings.ToLower(snake)
}

// MakeFieldMapFromStruct converte um struct (ou *struct) em FieldMap.
//   - Retorna erro se o input não for struct/ptr.
//   - Usa tags `db:"nome_coluna"` se presentes.
func MakeFieldMapFromStruct(i any, tag string) (FieldMap, error) {
	if i == nil {
		return nil, errors.New("input is nil")
	}

	v := reflect.ValueOf(i)
	if v.Kind() == reflect.Pointer {
		if v.IsNil() {
			return nil, errors.New("nil pointer provided")
		}
		v = v.Elem()
	}

	if v.Kind() != reflect.Struct {
		return nil, errors.New("expect struct or *struct")
	}

	t := v.Type()
	fm := make(FieldMap)

	for idx := 0; idx < t.NumField(); idx++ {
		field := t.Field(idx)
		val := v.Field(idx)

		// Ignora campos não exportados
		if field.PkgPath != "" { // unexported
			continue
		}

		// Ignora valor zero ou nil pointer
		if val.Kind() == reflect.Pointer && val.IsNil() {
			continue
		}

		// Trata sql.NullString e similares
		if ns, ok := val.Interface().(sql.NullString); ok {
			if !ns.Valid { // ignore not-valid
				continue
			}
			fm[columnName(field, tag)] = ns.String
			continue
		}

		// Generic IsZero (Go 1.20+)
		if val.IsZero() {
			continue
		}

		fm[columnName(field, tag)] = val.Interface()
	}

	return fm, nil
}

func columnName(f reflect.StructField, tag string) string {
	if tag, ok := f.Tag.Lookup(tag); ok && tag != "" && tag != "-" {
		return tag
	}
	return camelToSnake(f.Name)
}
