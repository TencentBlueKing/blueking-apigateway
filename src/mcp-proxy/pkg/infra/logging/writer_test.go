/*
 * TencentBlueKing is pleased to support the open source community by making
 * 蓝鲸智云 - API 网关(BlueKing - APIGateway) available.
 * Copyright (C) 2025 Tencent. All rights reserved.
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

package logging_test

import (
	"os"

	. "github.com/onsi/ginkgo/v2"
	. "github.com/onsi/gomega"

	"mcp_proxy/pkg/infra/logging"
)

var _ = Describe("Writer", func() {
	Describe("GetWriter with OS type", func() {
		DescribeTable("returns correct writer",
			func(settings map[string]string, expectError bool) {
				writer, err := logging.GetWriter("os", settings)
				if expectError {
					Expect(err).To(HaveOccurred())
				} else {
					Expect(err).NotTo(HaveOccurred())
					Expect(writer).NotTo(BeNil())
				}
			},
			Entry("stdout", map[string]string{"name": "stdout"}, false),
			Entry("stderr", map[string]string{"name": "stderr"}, false),
			Entry("unknown defaults to stdout", map[string]string{"name": "unknown"}, false),
			Entry("empty name defaults to stdout", map[string]string{}, false),
		)
	})

	Describe("GetWriter with unknown type", func() {
		It("should fallback to stdout", func() {
			writer, err := logging.GetWriter("unknown", map[string]string{})
			Expect(err).NotTo(HaveOccurred())
			Expect(writer).NotTo(BeNil())
			Expect(writer).To(Equal(os.Stdout))
		})
	})

	Describe("GetOSWriter", func() {
		DescribeTable("returns correct OS writer",
			func(settings map[string]string, expected *os.File) {
				writer, err := logging.GetOSWriter(settings)
				Expect(err).NotTo(HaveOccurred())
				Expect(writer).To(Equal(expected))
			},
			Entry("stdout", map[string]string{"name": "stdout"}, os.Stdout),
			Entry("stderr", map[string]string{"name": "stderr"}, os.Stderr),
			Entry("default to stdout", map[string]string{"name": "other"}, os.Stdout),
			Entry("empty settings", map[string]string{}, os.Stdout),
		)
	})

	Describe("GetFileWriter", func() {
		It("should fail with missing path", func() {
			settings := map[string]string{"name": "test.log"}
			_, err := logging.GetFileWriter(settings)
			Expect(err).To(HaveOccurred())
			Expect(err.Error()).To(ContainSubstring("path should not be empty"))
		})

		It("should fail with non-existent path", func() {
			settings := map[string]string{
				"path": "/non/existent/path",
				"name": "test.log",
			}
			_, err := logging.GetFileWriter(settings)
			Expect(err).To(HaveOccurred())
			Expect(err.Error()).To(ContainSubstring("not exists"))
		})

		It("should fail with invalid backups", func() {
			tempDir := GinkgoT().TempDir()
			settings := map[string]string{
				"path": tempDir, "name": "test.log", "backups": "invalid",
			}
			_, err := logging.GetFileWriter(settings)
			Expect(err).To(HaveOccurred())
			Expect(err.Error()).To(ContainSubstring("backups should be integer"))
		})

		It("should fail with invalid size", func() {
			tempDir := GinkgoT().TempDir()
			settings := map[string]string{
				"path": tempDir, "name": "test.log", "size": "invalid",
			}
			_, err := logging.GetFileWriter(settings)
			Expect(err).To(HaveOccurred())
			Expect(err.Error()).To(ContainSubstring("size should be integer"))
		})

		It("should fail with invalid age", func() {
			tempDir := GinkgoT().TempDir()
			settings := map[string]string{
				"path": tempDir, "name": "test.log", "age": "invalid",
			}
			_, err := logging.GetFileWriter(settings)
			Expect(err).To(HaveOccurred())
			Expect(err.Error()).To(ContainSubstring("age should be integer"))
		})

		It("should succeed with valid settings", func() {
			tempDir := GinkgoT().TempDir()
			settings := map[string]string{
				"path": tempDir, "name": "test.log",
				"backups": "5", "size": "100", "age": "30",
			}
			writer, err := logging.GetFileWriter(settings)
			Expect(err).NotTo(HaveOccurred())
			Expect(writer).NotTo(BeNil())
		})

		It("should succeed with default values", func() {
			tempDir := GinkgoT().TempDir()
			settings := map[string]string{
				"path": tempDir, "name": "test.log",
			}
			writer, err := logging.GetFileWriter(settings)
			Expect(err).NotTo(HaveOccurred())
			Expect(writer).NotTo(BeNil())
		})

		It("should handle path with trailing slash", func() {
			tempDir := GinkgoT().TempDir()
			settings := map[string]string{
				"path": tempDir + "/", "name": "test.log",
			}
			writer, err := logging.GetFileWriter(settings)
			Expect(err).NotTo(HaveOccurred())
			Expect(writer).NotTo(BeNil())
		})
	})

	Describe("GetWriter with file type", func() {
		It("should create file writer", func() {
			tempDir := GinkgoT().TempDir()
			settings := map[string]string{
				"path": tempDir, "name": "test.log",
			}
			writer, err := logging.GetWriter("file", settings)
			Expect(err).NotTo(HaveOccurred())
			Expect(writer).NotTo(BeNil())
		})
	})
})
