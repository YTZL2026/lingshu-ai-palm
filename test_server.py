from flask import Flask
app = Flask(__name__)

@app.route("/api/ping", methods=["GET"])
def ping():
    return {"has_search": True}

if __name__ == "__main__":
    # 打印路由确认注册
    print("===已加载路由===")
    for route in app.url_map.iter_rules():
        print(route)
    # 单进程、锁定本地回环、关闭调试重载
    try:
        app.run(host="127.0.0.1", port=8081, debug=False, use_reloader=False)
    except Exception as err:
        print("服务启动失败：", err)
    # 防止运行结束窗口闪退，加输入阻塞
    input("\n按回车键关闭窗口...")