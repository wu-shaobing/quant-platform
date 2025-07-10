import random
import base64
import logging
from io import BytesIO
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from PIL import Image, ImageDraw

router = APIRouter()
logger = logging.getLogger(__name__)

# 存储验证码答案（生产环境应使用Redis）
CAPTCHA_ANSWERS = {}

class SliderCaptchaData(BaseModel):
    captcha_id: str
    background_image: str
    slider_image: str

class VerificationData(BaseModel):
    captcha_id: str
    position: int

def create_slider_captcha():
    """生成滑块验证码"""
    try:
        logger.info("创建滑块验证码：开始")
        # 1. 创建背景图
        bg_image = Image.new('RGB', (300, 150), (255, 255, 255))
        draw = ImageDraw.Draw(bg_image)
        logger.info("创建滑块验证码：背景图已创建")

        # 2. 随机确定滑块位置
        slider_x = random.randint(100, 250)
        slider_y = random.randint(20, 100)
        slider_size = 40
        logger.info(f"创建滑块验证码：滑块位置 {slider_x}, {slider_y}")

        # 3. 从背景图中裁剪出滑块
        box = (slider_x, slider_y, slider_x + slider_size, slider_y + slider_size)
        slider_image = bg_image.crop(box)
        logger.info("创建滑块验证码：滑块已裁剪")

        # 4. 在背景图上挖空
        draw.rectangle(box, fill=(255, 255, 255))
        draw.rectangle(box, outline=(0, 0, 0), width=1)
        logger.info("创建滑块验证码：背景图已挖空")

        # 5. 将图片转为Base64
        bg_io = BytesIO()
        bg_image.save(bg_io, 'PNG')
        bg_base64 = "data:image/png;base64," + base64.b64encode(bg_io.getvalue()).decode()

        slider_io = BytesIO()
        slider_image.save(slider_io, 'PNG')
        slider_base64 = "data:image/png;base64," + base64.b64encode(slider_io.getvalue()).decode()
        logger.info("创建滑块验证码：图片已转为Base64")

        return bg_base64, slider_base64, slider_x
    except Exception as e:
        logger.error(f"创建滑块验证码失败: {e}", exc_info=True)
        raise

@router.get("/slider", response_model=SliderCaptchaData, summary="获取滑块验证码")
async def get_slider_captcha():
    logger.info("收到获取滑块验证码的请求")
    try:
        background_image, slider_image, position = create_slider_captcha()
        captcha_id = "captcha_" + str(random.randint(1000, 9999))
        CAPTCHA_ANSWERS[captcha_id] = position
        logger.info(f"成功创建验证码, ID: {captcha_id}")
        return {
            "captcha_id": captcha_id,
            "background_image": background_image,
            "slider_image": slider_image
        }
    except Exception as e:
        logger.error(f"[/slider] 端点处理异常: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="生成验证码时发生内部错误")

@router.post("/slider/verify", summary="校验滑块位置")
async def verify_slider_position(data: VerificationData):
    correct_position = CAPTCHA_ANSWERS.get(data.captcha_id)
    if correct_position is None:
        raise HTTPException(status_code=400, detail="验证码ID无效或已过期")

    # 允许一定的误差
    if abs(data.position - correct_position) <= 5:
        del CAPTCHA_ANSWERS[data.captcha_id]  # 验证成功后删除
        return {"message": "验证成功", "token": "dummy_verification_token"} # 返回一个临时的token
    else:
        raise HTTPException(status_code=400, detail="验证失败") 