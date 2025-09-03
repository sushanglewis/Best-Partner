使用Vue+React开发frontend，通过 http://localhost:5174/ 访问
默认进入landingpage
整体使用1920*1440分辨率，自适应
使用浅色背景、黑色字体。设计简约，禁止使用表情符号
## 1、landingpage

### top区域

高度80px，提供页面路由，如下排列
｜Best Partner｜首页｜模型管理｜会话｜

### 主视觉区（居中排列）

Best Partner
让人人都用好AI
输入控件：类似搜索引擎的控件，可以在此输入需求，默认占位文字“帮我做个ppt”｜按钮（文字内容为 GO，点击后调用http://localhost:8080/api/v1/requirements/submit 接口） human_message=当前输入框中的信息

## 2、模型管理

### top区域

高度80px，提供页面路由，如下排列
｜Best Partner｜首页｜模型管理｜会话｜

### 主视觉区，左侧为 模型配置 ｜ 右侧为 已保存模型列表

#### 模型配置

模型供应商，下拉选择，有deepseek、zhipuai、通义千问、月之暗面
base_url ：用户输入base_url
model ： 用户输入model参数
温度： 0～1，默认0.8
api_key ：用户输入 api_key
信息显示：显示测试按钮返回的信息
测试 按钮，点击后调用 http://localhost:8080/api/v1/models/test 接口，测试模型是否可用，成功后显示‘连接成功’，失败显示报错信息
保存 按钮，点击后调用 http://localhost:8080/api/v1/models/save 接口，保存模型配置
### 已保存模型列表

SELECT *
FROM public.model_settings
将获得的数据以卡片的形式纵向排列，默认选中第一个，用户可以单击切换选中模型。


## 3、workspace page



在landingpage页面点击GO按钮后，立即进入该页面，backend会返回消息体
{
  "thread_id": "string",
  "state_version": 0,
  "current_status": "string",
  "requirements_document": {
    "additionalProp1": {}
  },
  "question_list": [],
  "messages": [],
  "multi_files": []
}

使用消息体中的 thread_id、state_version 轮询 http://localhost:8080/api/v1/requirements/status 接口 每5s一次，并持续判断返回体中的 has_update 是否为true，如果为true 则停止轮询。并立即使用 thread_id 请求 http://localhost:8080/api/v1/requirements/state 接口，获取最新的状态，然后渲染主视觉区页面

### top区域

高度80px，提供页面路由，如下排列
｜Best Partner｜首页｜模型管理｜会话｜

### 主视觉区 ，高度铺满剩余空间，从左至右按照2:5:3的比例分割页面

#### 版本目录 (最左侧（历史版本）横向空间占十分之二)
通过 thread_id 查询postgresql数据库中的
SELECT version
FROM public.requirements_documents where thread = '当前的thread_id'，并按照时间顺序排序

#### worksapce 中间 markdown 编辑器，横向空间占十分之五
内容为当前所选版本的 requirements.content
SELECT content
FROM public.requirements_documents where thread = '当前的thread_id' and version = '版本目录当前选中的version'

#### Best-Partner-assistant 右侧，横向空间占十分之三
上半部分为 http://localhost:8080/api/v1/requirements/state 接口返回的state中的question_list 
问题content（内容为返回体中的 question_list.content[1]
选项1 （内容为 question_id=question_list[1].id 的 suggestion_option[1].content
选项2 （内容为 question_id=question_list[1].id 的 suggestion_option[2].content
选项3 （内容为 question_id=question_list[1].id 的 suggestion_option[3].content
选项4  ‘无需讨论’  ｜  选项5 '结合最佳实践提供建议'
问题content（内容为返回体中的 question_list.content[2]
选项1 （内容为 question_id=question_list[2].id 的 suggestion_option[1].content
选项2 （内容为 question_id=question_list[2].id 的 suggestion_option[2].content
选项3 （内容为 question_id=question_list[2].id 的 suggestion_option[3].content
选项4  ‘无需讨论’  ｜  选项5 '结合最佳实践提供建议'
问题content（内容为返回体中的 question_list.content[3]
选项1 （内容为 question_id=question_list[3].id 的 suggestion_option[1].content
选项2 （内容为 question_id=question_list[3].id 的 suggestion_option[2].content
选项3 （内容为 question_id=question_list[3].id 的 suggestion_option[3].content
选项4  ‘无需讨论’  ｜  选项5 '结合最佳实践提供建议'
用户输入窗口：长文本输入窗口 
提交按钮（点击后将当前 问题 与 问题下勾选的选项 进行拼接， 最后拼接上用户在窗口中输入的文本，共同作为human_message 调用 http://localhost:8080/api/v1/requirements/submit 接口 ，此时需要传入当前的thread_id 以及 state_version。

提交后使用消thread_id、state_version 轮询 http://localhost:8080/api/v1/requirements/status 接口 每5s一次，并持续判断返回体中的 has_update 是否为true，如果为true 则停止轮询。并立即使用 thread_id 请求 http://localhost:8080/api/v1/requirements/state 接口，获取最新的状态，并使用数据重新渲染版本目录、workspace、Best-Partner-assistant 三个区域




## 1. 登录页面 (P1)

### 1.1 页面布局
- 采用居中卡片布局，宽度为400px，圆角12px
- 背景使用浅色系统背景色 (#fbfbfd)，卡片背景为纯白色
- 卡片带有微妙阴影 (0 1px 3px rgba(0, 0, 0, 0.05)) 和1px边框 (rgba(0, 0, 0, 0.1))

### 1.2 页面元素
#### 1.2.1 系统标题
- 位置：卡片顶部，垂直间距适当增加
- 字体：24px，加粗 (600)，无衬线字体族
- 内容："Best Partner"

#### 1.2.2 Slogan
- 位置：标题下方，间距8px
- 字体：14px，颜色采用系统次级文本色
- 内容："让所有人都可以用好AI"

#### 1.2.3 用户名输入框
- 样式：圆角12px，微妙边框，内边距舒适
- 默认值：sushang
- 占位符：请输入用户名
- 宽度：100%
- 交互：聚焦时有细微边框色变化

#### 1.2.4 密码输入框
- 样式：与用户名输入框保持一致
- 类型：password
- 默认值：123456
- 占位符：请输入密码

#### 1.2.5 登录按钮
- 样式：圆角12px，主色调整为#007AFF
- 文字颜色：白色
- 宽度：100%
- 交互：悬停时亮度微调，点击时有短暂缩放效果(0.98)

#### 1.2.6 版权信息
- 位置：卡片底部，上边距增加
- 字体：12px，使用系统最浅文本色
- 内容："©2024 Best Partner Team"

#### 1.2.7 错误提示
- 样式：红色提示文字，出现在输入框下方
- 动画：平滑出现过渡效果

## 2. 主页 (Landing Page, P2)

### 2.1 页面布局
- 顶部导航栏固定，采用毛玻璃效果(backdrop-filter: blur(20px))和轻微透明度
- 主体内容居中，宽度60%
- 整体使用统一的无衬线字体族

### 2.2 页面元素
#### 2.2.1 顶部导航栏 (Container_N1)
- 左侧Logo+Slogan：可点击，使用系统主色和适当字重
- 右侧模型管理链接：文字"模型管理"，跳转至P3
- 用户信息下拉菜单：圆角设计，带有微妙阴影

#### 2.2.2 消息提示条 (Container_A1)
- 条件显示：无可用模型时出现
- 样式：使用警示颜色，圆角设计，毛玻璃效果
- 内容：提示文本+"模型配置"链接(跳转至P3)

#### 2.2.3 需求输入区 (Container_B1)
- 文本输入框：单行，圆角12px，类似Bing搜索样式
- 文件上传区：支持拖放/点击，圆角设计，有明确视觉反馈
- 提交按钮：使用图标+文字，主色#007AFF，圆角12px

#### 2.2.4 已上传文件列表 (Container_C1)
- 每项：圆角卡片设计，带有微妙阴影
- 删除图标：点击时有缩放反馈，平滑过渡
- 布局：整洁列表，适当间距

#### 2.2.5 过渡效果
- 成功响应后跳转至P4时使用渐现和轻微缩放过渡

## 3. 模型管理页面 (P3)

### 3.1 页面布局
- 顶部导航栏同P2，保持一致性
- 选项卡位于页面中上部，采用现代选项卡设计
- 主内容区响应选项卡切换，有平滑过渡效果

### 3.2 模型配置选项卡 (TAB1)
#### 3.2.1 表单容器 (Container_D1)
- 所有输入元素：统一圆角12px设计，微妙边框
- 下拉框：现代样式，与整体设计语言一致
- 温度滑块：自定义样式，与数字输入框视觉对齐

#### 3.2.2 操作按钮组 (Container_E1)
- 测试按钮：初始可用，主色#007AFF
- 保存按钮：初始禁用，测试通过后启用并有视觉变化
- 取消按钮：次级按钮样式
- 所有按钮：圆角12px，有悬停和点击反馈

#### 3.2.3 测试结果区域 (Container_F1)
- 成功：绿色提示，带有成功图标
- 失败：红色错误信息，带有错误图标
- 动画：平滑出现过渡

### 3.3 模型列表选项卡 (TAB2)
#### 3.3.1 模型卡片列表 (Container_G1)
- 卡片设计：圆角12px，微妙阴影，适当内边距
- 当前使用模型：有明显视觉标签，蓝色边框+勾选图标
- 交互：点击时有反馈，选中状态明确

## 4. 需求垂询页面 (P4)

### 4.1 页面布局
- 分左-中-右三栏布局，比例2:5:3
- 整体使用统一设计语言，保持视觉一致性

### 4.2 左侧历史区域
- 树状结构：现代折叠/展开设计，清晰视觉层次
- 历史项目：卡片式设计，适当间距
树状结构，可以收起、展开
历史需求列表数据为通过当前user_id查询postgresql的session表所查到的thread_id并关联message表获得最早的一条message记录，将其content字段作为需求列表的需求概述
历史文档版本，通过thread_id查询requirements_documents表，version_id 为版本号

点击version_id 用户输入区的内容切换为该版本对应的状态，数据通过thread_id、version_id通过requirements_documents表获取对应的content
### 4.3 中部当前需求文档
- Markdown编辑器：与现代设计语言融合，圆角边框
- 版本信息：清晰但不突兀的显示方式
版本号：使用 {requirements_version}

最后更新时间

文档内容区域为 Markdown编辑器，支持用户编辑当前的 requirements_documents。当frontend轮询到version_state变化时，并获取最新的requirements_documents，则将最新的requirements_document 填充到mardown区域
### 4.4 右侧交互区 (Container_H1)
#### 4.4.1 轮次指示器
- 醒目但不突兀的显示方式
- state_version 为当前轮次
#### 4.4.2 问卷清单 (Container_I1)
- 卡片设计：每问题一张卡片，圆角12px，微妙阴影
包含以下选项：
- 推荐样式：现代单选/多选设计 
- 按钮："无需关心此问题"采用次级按钮样式
- 文本输入框：统一设计语言



#### 4.4.3 用户输入区
- 多行文本输入框：统一设计语言
- 文件上传组件：小型化但保持一致设计
- 提交按钮：主色#007AFF，圆角12px，有交互反馈

## 5. 通用设计语言 (U2)

### 5.1 色彩系统
- 背景：浅模式使用#fbfbfd，深色模式使用#1d1d1f
- 表面：浅模式纯白色，深色模式#2c2c2e
- 主色：使用#007AFF替代原蓝色
- 文字：通过字重(300, 400, 600)和大小构建层级

### 5.2 形态与质感
- 圆角：统一使用12px圆角半径
- 阴影：微妙阴影(0 1px 3px rgba(0, 0, 0, 0.05))
- 毛玻璃效果：导航栏等元素使用backdrop-filter: blur(20px)

### 5.3 动效与交互反馈
- 过渡：所有交互使用0.2s ease-in-out过渡
- 按钮反馈：点击时有微妙缩放效果(transform: scale(0.98))
- 页面切换：平滑渐隐和轻微缩放过渡

### 5.4 字体系统
- 统一使用：-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif
- 通过字重而非颜色区分信息层级

