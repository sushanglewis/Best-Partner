使用Vue+React开发frontend，通过 http://localhost:5174/ 访问
默认进入landingpage
整体使用1920*1440分辨率，自适应
使用浅色背景、黑色字体。设计简约，禁止使用表情符号
## 1、landingpage

### top区域

高度80px，提供页面路由，如下排列
｜Best Partner｜首页｜模型管理｜Workspace｜

### 主视觉区（居中排列）

Best Partner
让人人都用好AI
输入控件：类似搜索引擎的控件，可以在此输入需求，默认占位文字“帮我做个ppt”｜按钮（文字内容为 GO，点击后调用http://localhost:8080/api/v1/requirements/submit 接口） human_message=当前输入框中的信息 , model_param为当前model页面选中的模型参数

## 2、模型管理

### top区域

高度80px，提供页面路由，如下排列
｜Best Partner｜首页｜模型管理｜Workspace｜

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
｜Best Partner｜首页｜模型管理｜Workspace｜

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
提交按钮（点击后将当前 问题 与 问题下勾选的选项 进行拼接， 最后拼接上用户在窗口中输入的文本，共同作为human_message 调用 http://localhost:8080/api/v1/requirements/submit 接口 ，此时需要传入当前的thread_id 以及 state_version。model_param为当前model页面选中的模型参数

提交后使用消thread_id、state_version 轮询 http://localhost:8080/api/v1/requirements/status 接口 每5s一次，并持续判断返回体中的 has_update 是否为true，如果为true 则停止轮询。并立即使用 thread_id 请求 http://localhost:8080/api/v1/requirements/state 接口，获取最新的状态，并使用数据重新渲染版本目录、workspace、Best-Partner-assistant 三个区域
