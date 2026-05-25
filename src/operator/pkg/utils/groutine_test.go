package utils

import (
	"io"
	"log"
	"testing"

	"github.com/getsentry/sentry-go"
)

func TestReportRecoveredPanicWithoutSentryClient(t *testing.T) {
	previousLogWriter := log.Writer()
	log.SetOutput(io.Discard)
	t.Cleanup(func() {
		log.SetOutput(previousLogWriter)
	})

	currentHub := sentry.CurrentHub()
	previousClient := currentHub.Client()
	currentHub.BindClient(nil)
	t.Cleanup(func() {
		currentHub.BindClient(previousClient)
	})

	reportRecoveredPanic()
}
