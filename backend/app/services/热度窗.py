from app.services import 时间


def 尝试关窗(conn, 房间键: str, 水位事件时: str, 允许迟到秒: int, 窗长秒: int, 处理时: str,
             切流代次: int | None = None) -> int:
    """水位 >= 窗止 时关闭开启窗（发射）；允许迟到只影响关闭后能否再修正，不推迟关闭。

    切流代次给出时只关本代次窗——旧代次窗已在切流事务里关尽，
    双保险防止重开后新场扫到历史窗。
    """
    del 允许迟到秒, 窗长秒  # 关窗只看水位与窗止
    关闭数 = 0
    if 切流代次 is None:
        rows = conn.execute(
            "SELECT * FROM 热度窗 WHERE 房间键=? AND 状态='开启' ORDER BY 窗起事件时",
            (房间键,),
        ).fetchall()
    else:
        rows = conn.execute(
            "SELECT * FROM 热度窗 WHERE 房间键=? AND 状态='开启' AND 切流代次=? ORDER BY 窗起事件时",
            (房间键, 切流代次),
        ).fetchall()
    for 窗 in rows:
        if 时间.解析(水位事件时) >= 时间.解析(窗["窗止事件时"]):
            conn.execute(
                "UPDATE 热度窗 SET 状态='已关闭', 关闭处理时=?, 版本=CASE WHEN 版本=0 THEN 1 ELSE 版本 END WHERE 窗键=?",
                (处理时, 窗["窗键"]),
            )
            关闭数 += 1
    return 关闭数


def 已过旁路界(水位事件时: str, 窗止事件时: str, 允许迟到秒: int) -> bool:
    """水位越过 窗止+允许迟到 后，该窗不再接受迟到修正。"""
    旁路界 = 时间.加秒(窗止事件时, 允许迟到秒)
    return 时间.解析(水位事件时) >= 时间.解析(旁路界)
