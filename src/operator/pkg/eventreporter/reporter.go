/*
 * TencentBlueKing is pleased to support the open source community by making
 * 蓝鲸智云 - API 网关(BlueKing - APIGateway) available.
 * Copyright (C) Tencent. All rights reserved.
 * Licensed under the MIT License (the "License"); you may not use this file except
 * in compliance with the License. You may obtain a copy of the License at
 *
 *     http://opensource.org/licenses/MIT
 *
 * Unless required by applicable law or agreed to in writing, software distributed under
 * the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND,
 * either express or implied. See the License for the specific language governing permissions and
 * limitations under the License.
 *
 * We undertake not to change the open source license (MIT license) applicable
 * to the current version of the project delivered to anyone in the future.
 */

// Package eventreporter ...
package eventreporter

import (
	"context"
	"log"
	"strings"
	"sync"
	"time"

	"github.com/spf13/cast"

	"operator/pkg/client"
	"operator/pkg/config"
	"operator/pkg/constant"
	"operator/pkg/entity"
	"operator/pkg/logging"
	"operator/pkg/utils"
)

var (
	reporter     *Reporter
	reporterOnce sync.Once
)

type reportEvent struct {
	ctx     context.Context
	release *entity.ReleaseInfo
	Event   constant.EventName
	status  constant.EventStatus
	detail  map[string]any
	// event timestamp
	ts int64
}

type versionProbe struct {
	chain    chan struct{} // control version probe concurrency
	timeout  time.Duration // control version probe timeout
	waitTime time.Duration // control version probe wait time
}

// Reporter is a struct that contains the event chain, report chain, close channel, and version probe.
type Reporter struct {
	eventChain   chan reportEvent
	reportChain  chan struct{} // control reporter concurrency
	close        chan struct{}
	versionProbe versionProbe
}

// InitReporter initializes the reporter
func InitReporter(cfg *config.Config) {
	reporterOnce.Do(func() {
		reporter = &Reporter{
			eventChain:  make(chan reportEvent, cfg.EventReporter.EventBufferSize),
			reportChain: make(chan struct{}, cfg.EventReporter.ReporterBufferSize),
			close:       make(chan struct{}),
			versionProbe: versionProbe{
				chain:    make(chan struct{}, cfg.EventReporter.VersionProbe.BufferSize),
				timeout:  cfg.EventReporter.VersionProbe.Timeout,
				waitTime: cfg.EventReporter.VersionProbe.WaitTime,
			},
		}
	})
}

// Start reporter
func Start(ctx context.Context) {
	utils.GoroutineWithRecovery(ctx, func() {
		for event := range reporter.eventChain {
			reporter.reportChain <- struct{}{}
			// Concurrent processing to avoid processing too slow
			tempEvent := event // Avoid closure problems
			utils.GoroutineWithRecovery(ctx, func() {
				reporter.reportEvent(tempEvent)
			})
		}
		reporter.close <- struct{}{}
		logging.GetLogger().Info("reporter exiting")
	})
}

// Shutdown shuts down the reporter
// Note: Here you need to close the eventChain data source committer first,
//
//	and then close the close, otherwise writing to the eventChain will panic
func Shutdown() {
	logging.GetLogger().Info("reporter  closing")
	ctx, cancel := context.WithTimeout(context.Background(), 20*time.Second)
	defer cancel()
	close(reporter.eventChain)
	select {
	case <-reporter.close:
		logging.GetLogger().Info("reporter closed")
	case <-ctx.Done():
		log.Println("close reporter timeout of 5 seconds")
	}
}

// ReportParseConfigurationDoingEvent  will report the event of paring configuration
func ReportParseConfigurationDoingEvent(ctx context.Context, release *entity.ReleaseInfo) {
	event := reportEvent{
		ctx:     ctx,
		release: release,
		Event:   constant.EventNameParseConfiguration,
		status:  constant.EventStatusDoing,
		detail:  nil,
		ts:      time.Now().Unix(),
	}
	addEvent(event)
}

// ReportParseConfigurationFailureEvent will report parse configuration failure event
func ReportParseConfigurationFailureEvent(ctx context.Context, release *entity.ReleaseInfo, err error) {
	event := reportEvent{
		ctx:     ctx,
		release: release,
		Event:   constant.EventNameParseConfiguration,
		status:  constant.EventStatusFailure,
		detail:  map[string]any{"err_msg": err.Error()},
		ts:      time.Now().Unix(),
	}
	addEvent(event)
}

// ReportParseConfigurationSuccessEvent will report the success event of parse configuration
func ReportParseConfigurationSuccessEvent(ctx context.Context, release *entity.ReleaseInfo) {
	event := reportEvent{
		ctx:     ctx,
		release: release,
		Event:   constant.EventNameParseConfiguration,
		status:  constant.EventStatusSuccess,
		ts:      time.Now().Unix(),
	}
	addEvent(event)
}

// ReportApplyConfigurationDoingEvent will report the event of applying configuration
func ReportApplyConfigurationDoingEvent(ctx context.Context, release *entity.ReleaseInfo) {
	event := reportEvent{
		ctx:     ctx,
		release: release,
		Event:   constant.EventNameApplyConfiguration,
		status:  constant.EventStatusDoing,
		ts:      time.Now().Unix(),
	}
	addEvent(event)
}

// ReportApplyConfigurationFailureEvent will report failure event when apply configuration failed
func ReportApplyConfigurationFailureEvent(ctx context.Context, release *entity.ReleaseInfo, err error) {
	event := reportEvent{
		ctx:     ctx,
		release: release,
		Event:   constant.EventNameApplyConfiguration,
		status:  constant.EventStatusFailure,
		detail:  map[string]any{"err_msg": err.Error()},
		ts:      time.Now().Unix(),
	}
	addEvent(event)
}

// ReportApplyConfigurationSuccessEvent will report success event when apply configuration successfully
func ReportApplyConfigurationSuccessEvent(ctx context.Context, release *entity.ReleaseInfo) {
	event := reportEvent{
		ctx:     ctx,
		release: release,
		Event:   constant.EventNameApplyConfiguration,
		status:  constant.EventStatusSuccess,
		ts:      time.Now().Unix(),
	}
	addEvent(event)
}

// ReportLoadConfigurationDoingEvent will report  event when loading configuration
func ReportLoadConfigurationDoingEvent(ctx context.Context, release *entity.ReleaseInfo) {
	event := reportEvent{
		ctx:     ctx,
		release: release,
		Event:   constant.EventNameLoadConfiguration,
		status:  constant.EventStatusDoing,
		ts:      time.Now().Unix(),
	}
	addEvent(event)
}

// ReportLoadConfigurationResultEvent Report the detection result of apisix loading
func ReportLoadConfigurationResultEvent(ctx context.Context, release *entity.ReleaseInfo, stageChan chan struct{}) {
	// filter not need report event
	if release == nil || release.Labels.PublishId == "" {
		<-stageChan
		return
	}
	if release.IsNoNeedReport() {
		<-stageChan
		logging.GetLogger().Debugf("event[release: %+v] is not need to report", release.Labels)
		return
	}

	reporter.versionProbe.chain <- struct{}{} // control concurrency
	utils.GoroutineWithRecovery(ctx, func() {
		defer func() {
			<-reporter.versionProbe.chain
			<-stageChan
		}()
		// wait apisix rebuild finished then begin version probe
		time.Sleep(reporter.versionProbe.waitTime)
		eventReq := parseEventInfo(release)
		reportCtx, cancelFunc := context.WithTimeout(ctx, reporter.versionProbe.timeout)
		errChan := make(chan error, 1)
		defer func() {
			cancelFunc()
			close(errChan)
		}()

		// publish probe
		utils.GoroutineWithRecovery(ctx, func() {
			// begin publish probe
			versionInfo, err := client.GetApisixClient().
				GetReleaseVersion(eventReq.BkGatewayName, eventReq.BkStageName, eventReq.PublishID)
			errChan <- err
			if err != nil {
				logging.GetLogger().Errorf(
					"get release[gateway:%s,release:%s,publish_id:%s] version from apisix err:%v",
					eventReq.BkGatewayName, eventReq.BkStageName, eventReq.PublishID, err)
				return
			}
			event := reportEvent{
				ctx:     ctx,
				release: release,
				Event:   constant.EventNameLoadConfiguration,
				status:  constant.EventStatusSuccess,
				detail: map[string]any{
					"publish_id": versionInfo.PublishID,
					"start_time": versionInfo.StartTime,
				},
				ts: time.Now().Unix(),
			}
			reporter.eventChain <- event
		})
		select {
		case err := <-errChan:
			if err != nil {
				event := reportEvent{
					ctx:     ctx,
					release: release,
					Event:   constant.EventNameLoadConfiguration,
					status:  constant.EventStatusFailure,
					detail:  map[string]any{"err_msg": err.Error()},
					ts:      time.Now().Unix(),
				}
				reporter.eventChain <- event
			}
			return
		case <-reportCtx.Done():
			// version publish probe timeout
			event := reportEvent{
				ctx:     ctx,
				release: release,
				Event:   constant.EventNameLoadConfiguration,
				status:  constant.EventStatusFailure,
				detail:  map[string]any{"err_msg": "version publish probe timeout"},
				ts:      time.Now().Unix(),
			}
			reporter.eventChain <- event
		}
	})
}

// addEvent add event to reporter event
func addEvent(event reportEvent) {
	// avoid gateway del that cause release to be nil and make panic
	if event.release == nil || event.release.Labels.PublishId == "" {
		return
	}
	if event.release.IsNoNeedReport() {
		logging.GetLogger().Debugf("event[release: %+v] is not need to report", event.release.Labels)
		return
	}
	reporter.eventChain <- event
}

// reportEvent
func (r *Reporter) reportEvent(event reportEvent) {
	defer func() {
		<-r.reportChain
	}()
	if event.release == nil {
		logging.GetLogger().Errorf("event[%+v]release is empty", event)
		return
	}

	// parse event info
	eventReq := parseEventInfo(event.release)
	eventReq.Name = event.Event
	eventReq.Status = event.status
	eventReq.Ts = event.ts
	if len(event.detail) != 0 {
		eventReq.Detail = event.detail
	}

	// report event
	err := client.GetCoreAPIClient().ReportPublishEvent(context.TODO(), eventReq)
	if err != nil && !strings.Contains(err.Error(), constant.EventDuplicatedErrMsg) {
		logging.GetLogger().Errorf(
			"report event  [name:%s,gateway:%s,release:%s,publish_id:%s,status:%s] fail:%v",
			event.Event,
			eventReq.BkGatewayName,
			eventReq.BkStageName,
			eventReq.PublishID,
			event.status,
			err,
		)
		return
	}

	// log event
	logging.GetLogger().Infof("report event [name:%s,gateway:%s,release:%s,publish_id:%s,status:%s] success",
		event.Event, eventReq.BkGatewayName, eventReq.BkStageName, eventReq.PublishID, event.status)
}

// parseEventInfo parse release info
func parseEventInfo(release *entity.ReleaseInfo) *client.ReportEventReq {
	gatewayName := release.GetGatewayName()
	stageName := release.GetStageName()
	publishID := cast.ToString(release.PublishId)
	return &client.ReportEventReq{
		BkGatewayName: gatewayName,
		BkStageName:   stageName,
		PublishID:     publishID,
	}
}
