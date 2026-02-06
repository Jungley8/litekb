/**
 * E2E 测试 - Playwright
 */
import { test, expect } from '@playwright/test';

// ========== 测试配置 ==========

test.describe('LiteKB E2E Tests', () => {
  
  // ========== 首页测试 ==========
  
  test.describe('Home Page', () => {
    test('should load home page', async ({ page }) => {
      await page.goto('/');
      await expect(page.locator('text=LiteKB')).toBeVisible();
    });
    
    test('should show statistics cards', async ({ page }) => {
      await page.goto('/');
      await expect(page.locator('text=知识库数量')).toBeVisible();
      await expect(page.locator('text=文档总数')).toBeVisible();
    });
    
    test('should navigate to knowledge bases', async ({ page }) => {
      await page.goto('/');
      await page.click('text=知识库');
      await expect(page.locator('h2:has-text("知识库")')).toBeVisible();
    });
  });
  
  // ========== 知识库测试 ==========
  
  test.describe('Knowledge Bases', () => {
    test('should display empty state when no KB', async ({ page }) => {
      await page.goto('/kbs');
      await expect(page.locator('text=还没有知识库')).toBeVisible();
    });
    
    test('should create a new knowledge base', async ({ page }) => {
      await page.goto('/kbs');
      
      // 点击创建按钮
      await page.click('text=新建知识库');
      
      // 填写表单
      await page.fill('input[placeholder="输入知识库名称"]', 'Test KB');
      await page.fill('textarea[placeholder="简单描述"]', 'Test Description');
      
      // 提交
      await page.click('button:has-text("创建")');
      
      // 验证创建成功
      await expect(page.locator('text=Test KB')).toBeVisible();
    });
    
    test('should navigate to KB detail', async ({ page }) => {
      await page.goto('/kbs');
      await page.click('text=Test KB');
      await expect(page.locator('h2:has-text("Test KB")')).toBeVisible();
    });
  });
  
  // ========== 文档上传测试 ==========
  
  test.describe('Document Upload', () => {
    test('should show upload dialog', async ({ page }) => {
      await page.goto('/kbs');
      await page.click('text=Test KB');
      await page.click('text=上传文档');
      await expect(page.locator('text=点击或拖拽文件到此处上传')).toBeVisible();
    });
    
    test('should upload markdown file', async ({ page }) => {
      await page.goto('/kbs');
      await page.click('text=Test KB');
      await page.click('text=上传文档');
      
      // 模拟文件上传 (实际需要处理文件)
      // await page.setInputFiles('input[type="file"]', 'test.md');
    });
  });
  
  // ========== RAG 对话测试 ==========
  
  test.describe('RAG Chat', () => {
    test('should display chat interface', async ({ page }) => {
      await page.goto('/chat');
      await expect(page.locator('text=开始与知识库对话吧')).toBeVisible();
    });
    
    test('should send message and get response', async ({ page }) => {
      await page.goto('/chat');
      
      // 选择知识库
      await page.click('.n-base-selection');
      await page.click('text=Test KB');
      
      // 输入问题
      await page.fill(
        'textarea[placeholder="输入问题，按 Enter 发送"]',
        '什么是人工智能？'
      );
      
      // 发送
      await page.click('button:has-text("发送")');
      
      // 等待加载
      await expect(page.locator('text=正在思考...')).toBeVisible();
      
      // 验证回答
      await expect(page.locator('.message.assistant')).toBeVisible();
    });
  });
  
  // ========== 搜索测试 ==========
  
  test.describe('Search', () => {
    test('should display search interface', async ({ page }) => {
      await page.goto('/search');
      await expect(page.locator('input[placeholder="搜索知识库..."]')).toBeVisible();
    });
    
    test('should perform search', async ({ page }) => {
      await page.goto('/search');
      await page.fill('input[placeholder="搜索知识库..."]', '人工智能');
      await page.click('button:has-text("搜索")');
      
      // 等待结果
      await expect(page.locator('text=找到')).toBeVisible();
    });
  });
  
  // ========== 知识图谱测试 ==========
  
  test.describe('Knowledge Graph', () => {
    test('should display graph visualization', async ({ page }) => {
      await page.goto('/graph');
      await expect(page.locator('svg.graph-svg')).toBeVisible();
    });
    
    test('should show node details on click', async ({ page }) => {
      await page.goto('/graph');
      await page.click('circle');
      await expect(page.locator('.node-detail')).toBeVisible();
    });
  });
  
  // ========== 设置测试 ==========
  
  test.describe('Settings', () => {
    test('should display settings page', async ({ page }) => {
      await page.goto('/settings');
      await expect(page.locator('text=LLM 设置')).toBeVisible();
    });
    
    test('should switch tabs', async ({ page }) => {
      await page.goto('/settings');
      await page.click('text=Embedding 设置');
      await expect(page.locator('text=Embedding 设置')).toBeVisible();
    });
  });
  
  // ========== 响应式测试 ==========
  
  test.describe('Responsive', () => {
    test('should work on mobile', async ({ page }) => {
      await page.setViewportSize({ width: 375, height: 667 });
      await page.goto('/');
      await expect(page.locator('.mobile-header')).toBeVisible();
    });
    
    test('should show mobile menu', async ({ page }) => {
      await page.setViewportSize({ width: 375, height: 667 });
      await page.goto('/');
      await page.click('.mobile-header .n-button');
      await expect(page.locator('.n-drawer')).toBeVisible();
    });
  });
  
  // ========== 深色模式测试 ==========
  
  test.describe('Dark Mode', () => {
    test('should toggle dark mode', async ({ page }) => {
      await page.goto('/');
      
      // 点击主题切换
      await page.click('button:has-text("深色模式")');
      
      // 验证深色模式启用
      await expect(page.locator('.dark-mode')).toBeVisible();
      
      // 切换回浅色
      await page.click('button:has-text("浅色模式")');
      await expect(page.locator('.dark-mode')).not.toBeVisible();
    });
  });
});

// ========== API 测试 ==========

test.describe('API Tests', () => {
  test('should return 200 on health check', async ({ request }) => {
    const response = await request.get('/health');
    expect(response.status()).toBe(200);
  });
  
  test('should return 401 without auth', async ({ request }) => {
    const response = await request.get('/api/v1/kb');
    expect(response.status()).toBe(401);
  });
});

// ========== 性能测试 ==========

test.describe('Performance', () => {
  test('should load page within 3s', async ({ page }) => {
    await page.goto('/', { waitUntil: 'networkidle' });
    
    const performanceTiming = await page.evaluate(() => {
      const timing = performance.timing;
      return timing.loadEventEnd - timing.navigationStart;
    });
    
    expect(performanceTiming).toBeLessThan(3000);
  });
});
