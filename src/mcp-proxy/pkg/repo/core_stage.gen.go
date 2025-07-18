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

// Code generated by gorm.io/gen. DO NOT EDIT.
// Code generated by gorm.io/gen. DO NOT EDIT.
// Code generated by gorm.io/gen. DO NOT EDIT.

package repo

import (
	"context"
	"database/sql"

	"gorm.io/gorm"
	"gorm.io/gorm/clause"
	"gorm.io/gorm/schema"

	"gorm.io/gen"
	"gorm.io/gen/field"

	"gorm.io/plugin/dbresolver"

	"mcp_proxy/pkg/entity/model"
)

func newStage(db *gorm.DB, opts ...gen.DOOption) stage {
	_stage := stage{}

	_stage.stageDo.UseDB(db, opts...)
	_stage.stageDo.UseModel(&model.Stage{})

	tableName := _stage.stageDo.TableName()
	_stage.ALL = field.NewAsterisk(tableName)
	_stage.ID = field.NewInt(tableName, "id")
	_stage.Name = field.NewString(tableName, "name")

	_stage.fillFieldMap()

	return _stage
}

type stage struct {
	stageDo stageDo

	ALL  field.Asterisk
	ID   field.Int
	Name field.String

	fieldMap map[string]field.Expr
}

func (s stage) Table(newTableName string) *stage {
	s.stageDo.UseTable(newTableName)
	return s.updateTableName(newTableName)
}

func (s stage) As(alias string) *stage {
	s.stageDo.DO = *(s.stageDo.As(alias).(*gen.DO))
	return s.updateTableName(alias)
}

func (s *stage) updateTableName(table string) *stage {
	s.ALL = field.NewAsterisk(table)
	s.ID = field.NewInt(table, "id")
	s.Name = field.NewString(table, "name")

	s.fillFieldMap()

	return s
}

func (s *stage) WithContext(ctx context.Context) IStageDo { return s.stageDo.WithContext(ctx) }

func (s stage) TableName() string { return s.stageDo.TableName() }

func (s stage) Alias() string { return s.stageDo.Alias() }

func (s stage) Columns(cols ...field.Expr) gen.Columns { return s.stageDo.Columns(cols...) }

func (s *stage) GetFieldByName(fieldName string) (field.OrderExpr, bool) {
	_f, ok := s.fieldMap[fieldName]
	if !ok || _f == nil {
		return nil, false
	}
	_oe, ok := _f.(field.OrderExpr)
	return _oe, ok
}

func (s *stage) fillFieldMap() {
	s.fieldMap = make(map[string]field.Expr, 2)
	s.fieldMap["id"] = s.ID
	s.fieldMap["name"] = s.Name
}

func (s stage) clone(db *gorm.DB) stage {
	s.stageDo.ReplaceConnPool(db.Statement.ConnPool)
	return s
}

func (s stage) replaceDB(db *gorm.DB) stage {
	s.stageDo.ReplaceDB(db)
	return s
}

type stageDo struct{ gen.DO }

type IStageDo interface {
	gen.SubQuery
	Debug() IStageDo
	WithContext(ctx context.Context) IStageDo
	WithResult(fc func(tx gen.Dao)) gen.ResultInfo
	ReplaceDB(db *gorm.DB)
	ReadDB() IStageDo
	WriteDB() IStageDo
	As(alias string) gen.Dao
	Session(config *gorm.Session) IStageDo
	Columns(cols ...field.Expr) gen.Columns
	Clauses(conds ...clause.Expression) IStageDo
	Not(conds ...gen.Condition) IStageDo
	Or(conds ...gen.Condition) IStageDo
	Select(conds ...field.Expr) IStageDo
	Where(conds ...gen.Condition) IStageDo
	Order(conds ...field.Expr) IStageDo
	Distinct(cols ...field.Expr) IStageDo
	Omit(cols ...field.Expr) IStageDo
	Join(table schema.Tabler, on ...field.Expr) IStageDo
	LeftJoin(table schema.Tabler, on ...field.Expr) IStageDo
	RightJoin(table schema.Tabler, on ...field.Expr) IStageDo
	Group(cols ...field.Expr) IStageDo
	Having(conds ...gen.Condition) IStageDo
	Limit(limit int) IStageDo
	Offset(offset int) IStageDo
	Count() (count int64, err error)
	Scopes(funcs ...func(gen.Dao) gen.Dao) IStageDo
	Unscoped() IStageDo
	Create(values ...*model.Stage) error
	CreateInBatches(values []*model.Stage, batchSize int) error
	Save(values ...*model.Stage) error
	First() (*model.Stage, error)
	Take() (*model.Stage, error)
	Last() (*model.Stage, error)
	Find() ([]*model.Stage, error)
	FindInBatch(batchSize int, fc func(tx gen.Dao, batch int) error) (results []*model.Stage, err error)
	FindInBatches(result *[]*model.Stage, batchSize int, fc func(tx gen.Dao, batch int) error) error
	Pluck(column field.Expr, dest interface{}) error
	Delete(...*model.Stage) (info gen.ResultInfo, err error)
	Update(column field.Expr, value interface{}) (info gen.ResultInfo, err error)
	UpdateSimple(columns ...field.AssignExpr) (info gen.ResultInfo, err error)
	Updates(value interface{}) (info gen.ResultInfo, err error)
	UpdateColumn(column field.Expr, value interface{}) (info gen.ResultInfo, err error)
	UpdateColumnSimple(columns ...field.AssignExpr) (info gen.ResultInfo, err error)
	UpdateColumns(value interface{}) (info gen.ResultInfo, err error)
	UpdateFrom(q gen.SubQuery) gen.Dao
	Attrs(attrs ...field.AssignExpr) IStageDo
	Assign(attrs ...field.AssignExpr) IStageDo
	Joins(fields ...field.RelationField) IStageDo
	Preload(fields ...field.RelationField) IStageDo
	FirstOrInit() (*model.Stage, error)
	FirstOrCreate() (*model.Stage, error)
	FindByPage(offset int, limit int) (result []*model.Stage, count int64, err error)
	ScanByPage(result interface{}, offset int, limit int) (count int64, err error)
	Rows() (*sql.Rows, error)
	Row() *sql.Row
	Scan(result interface{}) (err error)
	Returning(value interface{}, columns ...string) IStageDo
	UnderlyingDB() *gorm.DB
	schema.Tabler
}

func (s stageDo) Debug() IStageDo {
	return s.withDO(s.DO.Debug())
}

func (s stageDo) WithContext(ctx context.Context) IStageDo {
	return s.withDO(s.DO.WithContext(ctx))
}

func (s stageDo) ReadDB() IStageDo {
	return s.Clauses(dbresolver.Read)
}

func (s stageDo) WriteDB() IStageDo {
	return s.Clauses(dbresolver.Write)
}

func (s stageDo) Session(config *gorm.Session) IStageDo {
	return s.withDO(s.DO.Session(config))
}

func (s stageDo) Clauses(conds ...clause.Expression) IStageDo {
	return s.withDO(s.DO.Clauses(conds...))
}

func (s stageDo) Returning(value interface{}, columns ...string) IStageDo {
	return s.withDO(s.DO.Returning(value, columns...))
}

func (s stageDo) Not(conds ...gen.Condition) IStageDo {
	return s.withDO(s.DO.Not(conds...))
}

func (s stageDo) Or(conds ...gen.Condition) IStageDo {
	return s.withDO(s.DO.Or(conds...))
}

func (s stageDo) Select(conds ...field.Expr) IStageDo {
	return s.withDO(s.DO.Select(conds...))
}

func (s stageDo) Where(conds ...gen.Condition) IStageDo {
	return s.withDO(s.DO.Where(conds...))
}

func (s stageDo) Order(conds ...field.Expr) IStageDo {
	return s.withDO(s.DO.Order(conds...))
}

func (s stageDo) Distinct(cols ...field.Expr) IStageDo {
	return s.withDO(s.DO.Distinct(cols...))
}

func (s stageDo) Omit(cols ...field.Expr) IStageDo {
	return s.withDO(s.DO.Omit(cols...))
}

func (s stageDo) Join(table schema.Tabler, on ...field.Expr) IStageDo {
	return s.withDO(s.DO.Join(table, on...))
}

func (s stageDo) LeftJoin(table schema.Tabler, on ...field.Expr) IStageDo {
	return s.withDO(s.DO.LeftJoin(table, on...))
}

func (s stageDo) RightJoin(table schema.Tabler, on ...field.Expr) IStageDo {
	return s.withDO(s.DO.RightJoin(table, on...))
}

func (s stageDo) Group(cols ...field.Expr) IStageDo {
	return s.withDO(s.DO.Group(cols...))
}

func (s stageDo) Having(conds ...gen.Condition) IStageDo {
	return s.withDO(s.DO.Having(conds...))
}

func (s stageDo) Limit(limit int) IStageDo {
	return s.withDO(s.DO.Limit(limit))
}

func (s stageDo) Offset(offset int) IStageDo {
	return s.withDO(s.DO.Offset(offset))
}

func (s stageDo) Scopes(funcs ...func(gen.Dao) gen.Dao) IStageDo {
	return s.withDO(s.DO.Scopes(funcs...))
}

func (s stageDo) Unscoped() IStageDo {
	return s.withDO(s.DO.Unscoped())
}

func (s stageDo) Create(values ...*model.Stage) error {
	if len(values) == 0 {
		return nil
	}
	return s.DO.Create(values)
}

func (s stageDo) CreateInBatches(values []*model.Stage, batchSize int) error {
	return s.DO.CreateInBatches(values, batchSize)
}

// Save : !!! underlying implementation is different with GORM
// The method is equivalent to executing the statement: db.Clauses(clause.OnConflict{UpdateAll: true}).Create(values)
func (s stageDo) Save(values ...*model.Stage) error {
	if len(values) == 0 {
		return nil
	}
	return s.DO.Save(values)
}

func (s stageDo) First() (*model.Stage, error) {
	if result, err := s.DO.First(); err != nil {
		return nil, err
	} else {
		return result.(*model.Stage), nil
	}
}

func (s stageDo) Take() (*model.Stage, error) {
	if result, err := s.DO.Take(); err != nil {
		return nil, err
	} else {
		return result.(*model.Stage), nil
	}
}

func (s stageDo) Last() (*model.Stage, error) {
	if result, err := s.DO.Last(); err != nil {
		return nil, err
	} else {
		return result.(*model.Stage), nil
	}
}

func (s stageDo) Find() ([]*model.Stage, error) {
	result, err := s.DO.Find()
	return result.([]*model.Stage), err
}

func (s stageDo) FindInBatch(batchSize int, fc func(tx gen.Dao, batch int) error) (results []*model.Stage, err error) {
	buf := make([]*model.Stage, 0, batchSize)
	err = s.DO.FindInBatches(&buf, batchSize, func(tx gen.Dao, batch int) error {
		defer func() { results = append(results, buf...) }()
		return fc(tx, batch)
	})
	return results, err
}

func (s stageDo) FindInBatches(result *[]*model.Stage, batchSize int, fc func(tx gen.Dao, batch int) error) error {
	return s.DO.FindInBatches(result, batchSize, fc)
}

func (s stageDo) Attrs(attrs ...field.AssignExpr) IStageDo {
	return s.withDO(s.DO.Attrs(attrs...))
}

func (s stageDo) Assign(attrs ...field.AssignExpr) IStageDo {
	return s.withDO(s.DO.Assign(attrs...))
}

func (s stageDo) Joins(fields ...field.RelationField) IStageDo {
	for _, _f := range fields {
		s = *s.withDO(s.DO.Joins(_f))
	}
	return &s
}

func (s stageDo) Preload(fields ...field.RelationField) IStageDo {
	for _, _f := range fields {
		s = *s.withDO(s.DO.Preload(_f))
	}
	return &s
}

func (s stageDo) FirstOrInit() (*model.Stage, error) {
	if result, err := s.DO.FirstOrInit(); err != nil {
		return nil, err
	} else {
		return result.(*model.Stage), nil
	}
}

func (s stageDo) FirstOrCreate() (*model.Stage, error) {
	if result, err := s.DO.FirstOrCreate(); err != nil {
		return nil, err
	} else {
		return result.(*model.Stage), nil
	}
}

func (s stageDo) FindByPage(offset int, limit int) (result []*model.Stage, count int64, err error) {
	result, err = s.Offset(offset).Limit(limit).Find()
	if err != nil {
		return
	}

	if size := len(result); 0 < limit && 0 < size && size < limit {
		count = int64(size + offset)
		return
	}

	count, err = s.Offset(-1).Limit(-1).Count()
	return
}

func (s stageDo) ScanByPage(result interface{}, offset int, limit int) (count int64, err error) {
	count, err = s.Count()
	if err != nil {
		return
	}

	err = s.Offset(offset).Limit(limit).Scan(result)
	return
}

func (s stageDo) Scan(result interface{}) (err error) {
	return s.DO.Scan(result)
}

func (s stageDo) Delete(models ...*model.Stage) (result gen.ResultInfo, err error) {
	return s.DO.Delete(models)
}

func (s *stageDo) withDO(do gen.Dao) *stageDo {
	s.DO = *do.(*gen.DO)
	return s
}
