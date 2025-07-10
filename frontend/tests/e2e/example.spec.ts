import { test, expect } from '@playwright/test'

test.describe('量化投资平台', () => {
  test('首页应该正确加载', async ({ page }) => {
    await page.goto('/')
    
    // 检查页面标题
    await expect(page).toHaveTitle(/量化投资平台/)
    
    // 检查主要导航元素
    await expect(page.locator('nav')).toBeVisible()
    
    // 检查页面内容加载
    await expect(page.locator('main')).toBeVisible()
  })

  test('登录页面功能', async ({ page }) => {
    await page.goto('/login')
    
    // 检查登录表单元素
    await expect(page.locator('input[type="text"]')).toBeVisible()
    await expect(page.locator('input[type="password"]')).toBeVisible()
    await expect(page.locator('button[type="submit"]')).toBeVisible()
    
    // 测试表单验证
    await page.click('button[type="submit"]')
    // 应该显示验证错误信息
  })

  test('响应式设计', async ({ page }) => {
    await page.goto('/')
    
    // 测试移动端视图
    await page.setViewportSize({ width: 375, height: 667 })
    await expect(page.locator('nav')).toBeVisible()
    
    // 测试桌面端视图
    await page.setViewportSize({ width: 1280, height: 720 })
    await expect(page.locator('nav')).toBeVisible()
  })
}) 