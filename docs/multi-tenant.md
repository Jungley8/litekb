# LiteKB 多租户认证体系设计

## 一、数据模型

### 1. 组织 (Organization)
```sql
CREATE TABLE organizations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(200) NOT NULL,
    slug VARCHAR(100) UNIQUE NOT NULL,  -- 用于URL: litekb.com/{slug}/
    logo VARCHAR(500),
    settings JSONB DEFAULT '{}',  -- 组织配置
    plan VARCHAR(50) DEFAULT 'free',  -- free, pro, enterprise
    owner_id UUID REFERENCES users(id),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);
```

### 2. 用户扩展 (User)
```sql
ALTER TABLE users ADD COLUMN organization_id UUID REFERENCES organizations(id);
ALTER TABLE users ADD COLUMN role VARCHAR(50) DEFAULT 'member';  -- owner, admin, member
ALTER TABLE users ADD COLUMN is_active BOOLEAN DEFAULT TRUE;
```

### 3. 成员邀请 (Invitation)
```sql
CREATE TABLE invitations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID REFERENCES organizations(id),
    email VARCHAR(255) NOT NULL,
    role VARCHAR(50) DEFAULT 'member',
    token VARCHAR(100) UNIQUE NOT NULL,
    expires_at TIMESTAMP,
    status VARCHAR(20) DEFAULT 'pending',  -- pending, accepted, expired
    created_at TIMESTAMP DEFAULT NOW()
);
```

### 4. API Key (服务账号)
```sql
CREATE TABLE api_keys (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID REFERENCES organizations(id),
    name VARCHAR(200) NOT NULL,
    key_hash VARCHAR(255) NOT NULL,
    key_prefix VARCHAR(20) NOT NULL,  -- 用于显示: lkb_xxxx...
    scopes JSONB DEFAULT '["read"]',  -- read, write, admin
    last_used_at TIMESTAMP,
    expires_at TIMESTAMP,
    created_by UUID REFERENCES users(id),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT NOW()
);
```

## 二、认证方式

### 1. JWT 用户认证
```
POST /api/v1/auth/login
POST /api/v1/auth/register
POST /api/v1/auth/refresh
```

### 2. API Key 认证
```
Authorization: Bearer <token>
X-API-Key: <key_prefix>xxxx
```

### 3. 组织切换
```
Header: X-Organization-ID: <org_id>
```

## 三、权限模型

### 角色
| 角色 | 权限 |
|------|------|
| **owner** | 完全控制，包括删除组织 |
| **admin** | 管理成员，编辑设置 |
| **member** | 普通操作 |

### 权限检查
```python
# 权限定义
PERMISSIONS = {
    "kb:create": ["admin", "owner"],
    "kb:delete": ["owner"],
    "kb:manage": ["admin", "owner"],
    "doc:create": ["admin", "owner", "member"],
    "doc:delete": ["admin", "owner"],
    "member:invite": ["admin", "owner"],
    "member:remove": ["admin", "owner"],
    "settings:edit": ["admin", "owner"],
}
```

## 四、API 设计

### 组织管理
```
GET    /api/v1/organizations           # 列出用户所在组织
POST   /api/v1/organizations           # 创建组织
GET    /api/v1/organizations/{id}     # 获取组织详情
PUT    /api/v1/organizations/{id}     # 更新组织
DELETE /api/v1/organizations/{id}     # 删除组织

GET    /api/v1/organizations/{id}/members      # 成员列表
POST   /api/v1/organizations/{id}/invite      # 邀请成员
DELETE /api/v1/organizations/{id}/members/{uid} # 移除成员
PUT    /api/v1/organizations/{id}/members/{uid} # 更新角色
```

### API Key 管理
```
GET    /api/v1/organizations/{id}/api-keys           # 列出 Key
POST   /api/v1/organizations/{id}/api-keys           # 创建 Key
DELETE /api/v1/organizations/{id}/api-keys/{kid}     # 删除 Key
```

### 知识库作用域
```
# 组织内
GET /api/v1/kb                    # 当前组织知识库
POST /api/v1/kb                   # 在当前组织创建
GET /api/v1/kb/{id}              # 获取组织内知识库

# 跨组织 (需要权限)
GET /api/v1/organizations/{org_id}/kb/{kb_id}
```

## 五、实现步骤

1. **数据库模型** - 添加组织和多租户字段
2. **认证中间件** - 支持 JWT + API Key
3. **权限系统** - 基于角色的访问控制
4. **API 路由** - 组织管理接口
5. **前端集成** - 组织切换、成员管理

## 六、计费预留

```python
class OrganizationPlan:
    FREE = {
        "max_kb": 3,
        "max_docs": 1000,
        "max_members": 5,
        "vector_storage_gb": 1,
    }
    
    PRO = {
        "max_kb": 10,
        "max_docs": 50000,
        "max_members": 50,
        "vector_storage_gb": 10,
        "priority_support": True,
    }
    
    ENTERPRISE = {
        "unlimited": True,
        "sso": True,
        "audit_log": True,
    }
```
