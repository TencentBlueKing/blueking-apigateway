package utils

import (
	"testing"

	"operator/pkg/constant"
)

func TestToXVersion(t *testing.T) {
	tests := []struct {
		input    string
		expected constant.APISIXVersion
		hasError bool
	}{
		{"3.1", "3.1.X", false},
		{"3.2.1", "3.2.X", false},
		{"3", "", true},
		{"3.2.1.4", "", true},
	}

	for _, test := range tests {
		result, err := ToXVersion(test.input)
		if (err != nil) != test.hasError {
			t.Errorf("ToXVersion(%s) error = %v, expected error = %v", test.input, err, test.hasError)
		}
		if result != test.expected {
			t.Errorf("ToXVersion(%s) = %v, expected %v", test.input, result, test.expected)
		}
	}
}
