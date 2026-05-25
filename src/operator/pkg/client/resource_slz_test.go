package client

import (
	"encoding/json"
	"testing"

	"github.com/stretchr/testify/assert"
	"github.com/stretchr/testify/require"

	"operator/pkg/entity"
)

func TestStageScopedApisixResourcesUnmarshalsSSLs(t *testing.T) {
	resources := map[string]*entity.ApisixStageResource{
		"bk.release.gateway.stage": {
			SSLs: map[string]*entity.SSL{
				"ssl-1": {
					Cert: "cert",
					Key:  "key",
					Snis: []string{"example.com"},
				},
			},
		},
	}

	raw, err := json.Marshal(resources)
	require.NoError(t, err)

	var got ApisixListInfo
	require.NoError(t, json.Unmarshal(raw, &got))

	require.Contains(t, got, "bk.release.gateway.stage")
	assert.Equal(t, []string{"example.com"}, got["bk.release.gateway.stage"].SSLs["ssl-1"].Snis)
}
