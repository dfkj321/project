import streamlit as st
import streamlit.components.v1 as components
import os

# 页面配置
st.set_page_config(
    page_title="智能助手",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="collapsed"  # 默认收起侧边栏，让界面更大气
)

# 设置页面样式
st.markdown("""
<style>
    /* 整体页面样式优化 */
    .main {
        background-color: #f8f9fa;
        padding: 0 !important;
        margin: 0 !important;
        max-width: 100% !important;
    }
    
    /* 隐藏默认的页面标题 */
    header {
        visibility: hidden;
    }
    
    /* 隐藏Streamlit底部元素 */
    footer {
        visibility: hidden;
    }
    
    /* 确保容器不限制宽度 */
    .block-container {
        max-width: 100% !important;
        padding-left: 0 !important;
        padding-right: 0 !important;
        padding-top: 0 !important;
        padding-bottom: 0 !important;
    }
    
    /* 设置内容区域左边距为0，防止左侧内容被截断 */
    .css-18e3th9 {
        padding-left: 0rem !important;
        padding-right: 0rem !important;
    }
    
    /* 移除不必要的间距 */
    .css-hxt7ib {
        padding-top: 0.5rem !important;
        padding-left: 0rem !important;
        padding-right: 0rem !important;
    }
    
    /* 确保组件占满宽度 */
    .element-container, .stComponent {
        width: 100% !important;
    }
    
    /* 减少元素间距 */
    .stAlert {
        padding-top: 0 !important;
        padding-bottom: 0 !important;
        margin-bottom: 0.3rem !important;
    }
</style>
""", unsafe_allow_html=True)

# 创建一个自定义HTML组件来加载Coze SDK，并优化其样式
def load_coze_sdk():
    # 使用中国区CDN的Coze SDK，优化UI
    coze_html = """
    <div style="width:100%; height:800px; overflow:hidden;">
        <!-- 引入中国区Coze SDK -->
        <script src="https://lf-cdn.coze.cn/obj/unpkg/flow-platform/chat-app-sdk/1.2.0-beta.6/libs/cn/index.js"></script>
        
        <!-- 创建聊天界面容器 -->
        <div id="coze-chat-container" style="width:100%; height:100%;"></div>
        
        <script>
            // 初始化SDK函数
            function initCozeSdk() {
                try {
                    // 使用新提供的初始化方式
                    window.cozeWebSDK = new CozeWebSDK.WebChatClient({
                        config: {
                            bot_id: '7492089336734056482',
                            container: document.getElementById('coze-chat-container')
                        },
                        componentProps: {
                            title: '智能股票分析助手',
                            height: '100%',
                            width: '94%',  // 限制宽度，避免超出容器
                            marginLeft: 'auto',
                            marginRight: 'auto',
                            botAvatarImg: 'https://cdn-icons-png.flaticon.com/512/4616/4616271.png',
                            userAvatarImg: 'https://cdn-icons-png.flaticon.com/512/1077/1077063.png',
                            messageItemMap: {
                                backgroundColor: 'transparent', 
                                botMessageBgColor: '#f0f2ff',
                                userMessageBgColor: '#e3f6fc', 
                                botMessageColor: '#333',
                                userMessageColor: '#333'
                            }
                        },
                        auth: {
                            type: 'token',
                            token: 'pat_ICZrHlBpwB0CBxfY141nBYkkYeFCLn8350bK50I15bVcpsvEQ7Nx5j1w0yNvOMYJ',
                            onRefreshToken: function() {
                                return 'pat_ICZrHlBpwB0CBxfY141nBYkkYeFCLn8350bK50I15bVcpsvEQ7Nx5j1w0yNvOMYJ';
                            }
                        }
                    });
                    
                    console.log('Coze SDK 初始化成功!');
                    
                } catch (error) {
                    console.error("初始化Coze SDK错误:", error);
                    document.getElementById('coze-chat-container').innerHTML = 
                        '<div style="padding: 20px; text-align: center;">' +
                        '<h3 style="margin-top: 100px; color: #666;">聊天界面初始化失败</h3>' +
                        '<p style="color: #888;">请确保您能访问 Coze 服务，然后刷新页面重试</p>' +
                        '<p style="color: #888; margin-top: 20px;">错误信息: ' + error.message + '</p>' +
                        '</div>';
                }
            }
            
            // DOM加载完成后初始化
            if (document.readyState === 'loading') {
                document.addEventListener('DOMContentLoaded', initCozeSdk);
            } else {
                initCozeSdk();
            }
        </script>
    </div>
    """
    return coze_html

# 使用原来的列布局比例
left_space, center_col, right_space = st.columns([0.05, 0.9, 0.05])

with center_col:
    # 警告信息 - 使文字更短
    st.warning("智能助手提供的建议仅供参考，不构成投资建议")
    
    # SDK模式聊天界面 - 增加高度
    components.html(load_coze_sdk(), height=820, scrolling=False) 