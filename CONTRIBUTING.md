# LiteKB 贡献指南

感谢您考虑为 LiteKB 贡献代码！

## 📋 目录

- [行为准则](#行为准则)
- [开始贡献](#开始贡献)
- [开发流程](#开发流程)
- [代码规范](#代码规范)
- [提交规范](#提交规范)
- [测试](#测试)
- [文档](#文档)

---

## 🤝 行为准则

请阅读 [CODE_OF_CONDUCT.md](./CODE_OF_CONDUCT.md) 了解我们的社区准则。

## 🚀 开始贡献

### 先决条件

- Git
- Python 3.10+
- Node.js 18+
- Docker (推荐)

### Fork 项目

1. 点击右上角的 **Fork** 按钮
2. 克隆您的 Fork:
   ```bash
   git clone https://github.com/YOUR_USERNAME/litekb.git
   cd litekb
   ```
3. 添加上游仓库:
   ```bash
   git remote add upstream https://github.com/original/litekb.git
   ```

### 创建开发分支

```bash
# 同步上游最新代码
git fetch upstream
git checkout develop
git merge upstream/develop

# 创建新分支
git checkout -b feature/your-feature-name
```

## 🔧 开发流程

### 1. 设置开发环境

```bash
# 后端
cd backend
python -m venv venv
source venv/bin/activate  # Linux/Mac
.\venv\Scripts\activate  # Windows
pip install -r requirements.txt

# 前端
cd frontend
npm install
```

### 2. 启动服务

```bash
# 后端 (终端 1)
cd backend
uvicorn app.main:app --reload

# 前端 (终端 2)
cd frontend
npm run dev
```

### 3. 进行修改

- 在 `backend/` 或 `frontend/` 中添加/修改代码
- 遵循代码规范
- 添加测试
- 更新文档

### 4. 提交修改

```bash
git add .
git commit -m "feat: 添加新功能"
git push origin feature/your-feature-name
```

### 5. 创建 Pull Request

1. 访问您的 Fork 页面
2. 点击 **Compare & pull request**
3. 填写 PR 模板
4. 提交 PR

## 📏 代码规范

### Python (后端)

```bash
# 代码检查
pip install flake8 black mypy
flake8 app/ --max-line-length=100
black --check app/
mypy app/
```

### TypeScript/Vue (前端)

```bash
# 代码检查
npm run lint
npm run typecheck
```

### Git 提交

遵循 [Conventional Commits](https://www.conventionalcommits.org/):

- `feat`: 新功能
- `fix`: Bug 修复
- `docs`: 文档更新
- `style`: 代码格式 (不影响功能)
- `refactor`: 重构
- `perf`: 性能优化
- `test`: 测试相关
- `chore`: 构建/工具/辅助功能

示例:
```
feat(auth): 添加 Google OAuth 登录
fix(search): 修复搜索结果排序问题
docs(readme): 更新安装说明
```

## 🧪 测试

### 运行测试

```bash
# 后端
cd backend
pytest tests/ -v

# 前端
cd frontend
npm run test
```

### 编写测试

#### Python 测试

```python
# tests/test_your_feature.py
import pytest

class TestYourFeature:
    def test_example(self):
        """测试示例"""
        assert True
```

#### 前端测试

```typescript
// components/__tests__/YourComponent.spec.ts
import { describe, it, expect } from 'vitest'

describe('YourComponent', () => {
  it('renders correctly', () => {
    expect(true).toBe(true)
  })
})
```

### 测试覆盖要求

- 新功能: **80%+** 覆盖
- Bug 修复: **需要测试**

## 📖 文档

- 更新 `README.md` 如果添加新功能
- 更新 `docs/` 如果添加新配置
- 添加代码注释 (尤其复杂逻辑)
- API 更改需更新 `docs/api.md`

## 🔍 Review 流程

1. **自动化检查**: CI 运行测试、lint、类型检查
2. **人工 Review**: 维护者会尽快 Review
3. **反馈**: 可能需要修改
4. **合并**: 批准后合并到 `develop`

## 💬 交流

- **Issue**: 报告 Bug 或建议功能
- **Discussion**: 讨论想法
- **PR**: 代码贡献

## 📝 提交规范模板

```markdown
## 描述
[简短描述修改内容]

## 类型
- [ ] Bug 修复
- [ ] 新功能
- [ ] 破坏性更改
- [ ] 文档更新

## 截图 (如适用)
[添加截图]

## 检查清单
- [ ] 代码通过 lint
- [ ] 测试通过
- [ ] 更新文档
- [ ] 注释代码
- [ ] 清理临时文件
```

---

再次感谢您的贡献！ 🎉
