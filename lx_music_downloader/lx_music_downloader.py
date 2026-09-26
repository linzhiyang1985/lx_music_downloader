import sqlite3
import os
import re
import requests

if os.name == 'nt':
    APP_HOME = '%APPDATA%/lx-music-desktop'
elif os.name == 'posix':
    USER_HOME = os.path.expanduser("~")
    APP_HOME = os.path.join(USER_HOME, ".config/lx-music-desktop")
DB_PATH = os.path.join(APP_HOME, "LxDatas/lx.data.db")

SQL_QUERY = """
select info.id as infId, info.name, info.source, url.url, info.singer, url.id as urlId
from music_url as url
left join my_list_music_info as info on url.id like info.id||'_%'
"""


def query_music_urls(db_path=DB_PATH, filters={}):
    """连接 lx-music-desktop 的 SQLite 数据库，查询 music_url 与 my_list_music_info 的关联数据。

    Args:
        db_path: SQLite 数据库文件路径。

    Returns:
        list[dict]: 查询结果列表，每个元素为字段名到值的映射。
    """
    conn = sqlite3.connect(db_path)
    if filters:
        where_clause = " and ".join([f"{k} like '{v.replace('*', '%')}'"  if '*' in v else f"{k} = '{v}'" for k, v in filters.items()])
        query = SQL_QUERY + f" where {where_clause}"
    else:
        query = SQL_QUERY
    
    try:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute(query)
        for row in cursor:
            yield dict(row)
        # rows = cursor.fetchall()
        # return [dict(row) for row in rows]
    finally:
        conn.close()

result_title = ['ID', '歌名', '歌手', '来源', 'URL']
query_name = ''
result_gen = None
result_cache = []
def list_result_page(page_num=0):
    global result_title
    global query_name, result_gen, result_cache

    PAGE_SIZE = 9

    if not result_gen:
        if query_name:
            filters = {"name": query_name}
        else:
            filters = {}
        result_gen = query_music_urls(filters=filters)
    
    if not (len(result_cache)//PAGE_SIZE >= page_num + 1):
        for row in result_gen:
            result_cache.append(row)
            if len(result_cache)//PAGE_SIZE >= page_num + 1:
                break
    
    page_content = result_cache[page_num * PAGE_SIZE: (page_num + 1) * PAGE_SIZE]
    # render
    print(f'{result_title[0]}. {result_title[1]} - {result_title[2]} ({result_title[3]}): {result_title[4]}')
    for i, row in enumerate(page_content):
        print(f"{i+1}. {row['name']} - {row['singer']} ({row['source']}): {row['url']}")

def query(name=''):
    global query_name
    global  result_cache, result_gen
    query_name = name
    result_cache.clear()
    result_gen = None

def clear():
    """清屏"""
    os.system('cls' if os.name == 'nt' else 'clear')

download_session = requests.Session()
HEADERS = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/153.0.0.0 Safari/537.36"}
def download(id):
    global result_cache, download_session, HEADERS

    if id - 1 < len(result_cache):
        song_info = result_cache[id - 1]
        url = song_info['url']
        name = song_info['name']
        try:
            response = download_session.get(url, headers=HEADERS)
            if response.status_code == 200:
                with open(f"{name}.mp3", "wb") as f:
                    f.write(response.content)
                print(f"已下载: {name}")
        except Exception as e:
            print(f"下载 {name} 失败: {e}")
    else:
        print("无效的ID")

def export_to_html():
    global result_cache

    with open("list.html", "w") as f:
        f.write(f"<html><head><title>歌曲列表</title></head><body><table border='0'>")
        f.write(f"<tr><th>{result_title[0]}</th><th>{result_title[1]}</th><th>{result_title[2]}</th><th>{result_title[3]}</th><th>{result_title[4]}</th></tr>")
        for row in result_cache:
            f.write(f"<tr><td>{row['infId']}</td><td><a href='{row['url']}' target='_blank'>{row['name']}</a></td><td>{row['singer']}</td><td>{row['source']}</td><td>{row['url']}</td></tr>")
        f.write("</table></body></html>")

def loop():
    try:
        while True:
            cmd = input("输入指令(h查看帮助):")
            if cmd:
                if cmd.startswith('/'):
                    query(cmd[1:])
                    page_index = 0
                    list_result_page(page_index)
                elif cmd == 'n' or cmd == 'N':
                    page_index += 1
                    clear()
                    list_result_page(page_index)
                elif cmd == 'p' or cmd == 'P':
                    page_index -= 1
                    clear()
                    list_result_page(page_index)
                elif re.match(r'^(d|D)[1-9]$', cmd):
                    download(int(cmd[1]))
                elif cmd == 'x' or cmd == 'X':
                    export_to_html()
                    print("列表已导出为list.html")
                elif cmd == 'h' or cmd == 'H':
                    print("帮助信息:")
                    print("h: 显示帮助信息")
                    print("/name: 查询指定歌名(不指定名字列出所有，支持*模糊查询)")
                    print("n: 下一页")
                    print("p: 上一页")
                    print("d[1-9]: 下载第1..9首歌曲")
                    print("x: 导出列表为HTML文件")
                    print("q: 退出程序")
                elif cmd == 'q' or cmd == 'Q':
                    print("再见，感谢使用！")
                    break
    except KeyboardInterrupt:
        print("程序退出")



if __name__ == "__main__":
    # result_gen = query_music_urls(filters={"name": "*心"})
    # # result_gen = query_music_urls()
    # counter =  0
    # for row in result_gen:
    #     print(row)
    #     counter += 1
    # print(f"共查询到 {counter} 条记录")
    loop()
