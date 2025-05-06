
from fastapi import HTTPException, APIRouter
import pymysql

from src.agentapi.entity.result import create_response
from src.agentapi.entity.user import UserRegister, UserLogin
from src.agentapi.utils.dbtool import mysql_pool  # 使用修改后的连接池工具
from src.agentapi.utils.login_utils import generate_captcha, get_password_hash, verify_password
import base64




router = APIRouter(prefix="/agent", tags=["agent"])

# 验证码生成端点
@router.get("/captcha")
def get_captcha():
    code, buffer = generate_captcha()
    try:
        with mysql_pool.get_conn() as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    "INSERT INTO captchas (code) VALUES (%s)",
                    (code,)
                )
                captcha_id = cursor.lastrowid
                conn.commit()

        # 将图片数据编码为Base64
        image_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
        image_data = f"data:image/png;base64,{image_base64}"

        # 使用封装函数返回响应
        return create_response("验证码生成成功", data={
            "image": image_data,
            "text": code
        })

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

                # 使用封装函数返回响应
                return create_response("注册成功")

    except pymysql.Error as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=f"数据库错误: {str(e)}")


# 登录端点
@router.post("/login")
def login(user: UserLogin):
    try:
        with mysql_pool.get_conn() as conn:
            with conn.cursor(pymysql.cursors.DictCursor) as cursor:
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

                # 使用封装函数返回响应
                return create_response("登录成功")

    except pymysql.Error as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=f"数据库错误: {str(e)}")
