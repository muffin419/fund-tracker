# 基金管家 - 个人基金管理系统

个人基金持仓管理 + AI投资顾问，数据每日自动更新。

## 在线访问

部署到 GitHub Pages 后，访问地址：
```
https://你的用户名.github.io/fund-tracker/
```

## 功能介绍

| 模块 | 说明 |
|------|------|
| 总览 | 资产统计、今日定投提醒、持仓方向分布 |
| 我的持仓 | 添加/删除基金、买卖交易、目标进度追踪 |
| 定投计划 | 设置每周定投日历、自动统计合计金额 |
| 投资顾问 | 催化剂日历、政策趋势、方向预测、基金推荐 |
| 交易记录 | 申购/赎回记录及到账时间预估 |

## 数据自动更新

每天北京时间早8点，GitHub Actions 自动运行：

1. 抓取各行业ETF真实涨跌幅数据
2. 重新计算18个方向的评分和排名
3. 更新推荐基金的最新净值和收益
4. 自动清理过期的催化剂事件
5. 提交更改并重新部署网页

也可随时在 Actions 页面手动触发更新。

## 本地使用

双击 `index.html` 即可在浏览器打开，所有数据保存在浏览器本地存储中。

## 文件说明

```
fund-tracker/
├── index.html          # 主页面（单文件，含HTML+CSS+JS+数据）
├── update_script.py    # 数据自动更新脚本
├── .github/
│   └── workflows/
│       └── update.yml  # GitHub Actions 定时任务
└── README.md           # 本文件
```

## 如何部署到自己的GitHub

### 第1步：创建仓库

1. 打开 https://github.com/new
2. 仓库名填 `fund-tracker`
3. 选择 **Public**
4. 不要勾选任何初始化选项，直接点 **Create repository**

### 第2步：上传文件

**方式A：网页上传（最简单）**

1. 在新仓库页面点 **Add file → Upload files**
2. 把本项目的3个文件拖进去：`index.html`、`update_script.py`、`.github/workflows/update.yml`
3. 点 **Commit changes**

**方式B：命令行上传**

```bash
git clone https://github.com/你的用户名/fund-tracker.git
cd fund-tracker
# 复制 index.html, update_script.py, .github/workflows/update.yml 到文件夹
git add .
git commit -m "init"
git push origin main
```

### 第3步：开启 GitHub Pages

1. 仓库页面点 **Settings**
2. 左侧菜单点 **Pages**
3. Source 选择 **Deploy from a branch**
4. Branch 选 `main`，文件夹选 `/(root)`
5. 点 **Save**
6. 等待1分钟，访问显示的链接

### 第4步：验证自动更新

1. 点仓库顶部的 **Actions** 标签
2. 点左侧 **Daily Fund Data Update**
3. 点右侧 **Run workflow → Run workflow** 手动运行一次
4. 等2-3分钟，看是否显示绿色勾
5. 成功后，每天早8点会自动更新

## 手动更新数据

如果不想用自动更新，也可以手动修改 `index.html` 中的 `MARKET_DATA`：

1. 用文本编辑器打开 `index.html`
2. 找到 `let MARKET_DATA=` 这一行
3. 修改其中的数字和文字
4. 保存后用浏览器打开查看效果

## 数据备份与恢复

- **导出**：网页上点 **"导出备份"** 按钮，下载JSON文件
- **导入**：点 **"导入恢复"** 按钮，选择之前下载的JSON文件
- 建议每月导出一次备份

## 注意事项

1. 首次打开网页时，会自动加载默认的16只基金数据
2. 个人持仓数据保存在浏览器 `localStorage` 中，换电脑需重新导入
3. 投资顾问数据内嵌在HTML中，由GitHub Actions每日自动更新
4. 基金代码查询依赖天天基金网API，偶尔可能超时

## 免责声明

本系统所有信息仅供参考，不构成投资建议。基金投资有风险，入市需谨慎。
