from fastapi import HTTPException, Response, APIRouter
import pymysql
from src.agentapi.entity.user import UserRegister, UserLogin
from src.agentapi.utils.dbtool import mysql_pool  # 使用修改后的连接池工具
from src.agentapi.utils.login_utils import generate_captcha, get_password_hash, verify_password

router = APIRouter(prefix="/agent", tags=["agent"])


# 生成验证码端点
@router.get("/captcha")
def get_captcha():
    code, buffer = generate_captcha()
    try:
        # 使用with语句自动管理连接
        with mysql_pool.get_conn() as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    "INSERT INTO captchas (code) VALUES (%s)",
                    (code,)
                )
                captcha_id = cursor.lastrowid
                conn.commit()  # 显式提交事务

            return Response(
                content=buffer.getvalue(),
                media_type="image/png",
                headers={"captcha_id": str(captcha_id)}
            )
    except pymysql.Error as e:
        raise HTTPException(status_code=500, detail=f"数据库错误: {str(e)}")


# 注册端点
@router.post("/register")
def register(user: UserRegister):
    try:
        with mysql_pool.get_conn() as conn:
            with conn.cursor() as cursor:
                # 验证验证码
                cursor.execute(
                    """SELECT * FROM captchas 
                    WHERE id = %s AND code = %s 
                    AND used = FALSE 
                    AND created_at >= NOW() - INTERVAL 5 MINUTE""",
                    (user.captcha_id, user.captcha_code)
                )
                if not cursor.fetchone():
                    raise HTTPException(status_code=400, detail="验证码无效或已过期")

                # 标记验证码为已使用
                cursor.execute(
                    "UPDATE captchas SET used = TRUE WHERE id = %s",
                    (user.captcha_id,)
                )

                # 检查用户名是否存在
                cursor.execute(
                    "SELECT id FROM users WHERE username = %s",
                    (user.username,)
                )
                if cursor.fetchone():
                    raise HTTPException(status_code=400, detail="用户名已存在")

                # 创建用户
                hashed_password = get_password_hash(user.password)
                cursor.execute(
                    "INSERT INTO users (username, hashed_password) VALUES (%s, %s)",
                    (user.username, hashed_password)
                )
                conn.commit()
                return {"message": "注册成功"}

    except pymysql.Error as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=f"数据库错误: {str(e)}")


# 登录端点
@router.post("/login")
def login(user: UserLogin):
    try:
        with mysql_pool.get_conn() as conn:
            with conn.cursor(pymysql.cursors.DictCursor) as cursor:  # 使用字典游标
                # 验证验证码
                cursor.execute(
                    """SELECT * FROM captchas 
                    WHERE id = %s 
                    AND code = %s 
                    AND used = FALSE 
                    AND created_at >= NOW() - INTERVAL 5 MINUTE""",
                    (user.captcha_id, user.captcha_code)
                )
                if not cursor.fetchone():
                    raise HTTPException(status_code=400, detail="验证码无效或已过期")

                # 标记验证码已使用
                cursor.execute(
                    "UPDATE captchas SET used = TRUE WHERE id = %s",
                    (user.captcha_id,)
                )

                # 验证用户凭证
                cursor.execute(
                    "SELECT * FROM users WHERE username = %s",
                    (user.username,)
                )
                db_user = cursor.fetchone()
                if not db_user or not verify_password(user.password, db_user["hashed_password"]):
                    raise HTTPException(status_code=401, detail="用户名或密码错误")

                conn.commit()
                return {"message": "登录成功"}

    except pymysql.Error as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=f"数据库错误: {str(e)}")