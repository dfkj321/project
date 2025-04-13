@echo off
echo 启动板块数据分析系统...
cd %~dp0
streamlit run app.py --server.port=8600
pause 