"""
将 mp4 文件分离为 mp3 文件：
1. 指定 seek start 和 time duration 分离音轨的音频
2. 直接分离音轨的音频
"""

import os
import ffmpeg
import re

class VideoAudioSplitter:
    def __init__(self):
        self.output_dir = "outputs/audio"
        os.makedirs(self.output_dir, exist_ok=True)

    def _validate_time_format(self, time_str):
        """验证时间格式是否正确 (HH:MM:SS)"""
        if not time_str:
            return True
        pattern = r'^([0-9]{2}):([0-9]{2}):([0-9]{2})$'
        if not re.match(pattern, time_str):
            raise ValueError("时间格式必须为 HH:MM:SS，例如 00:01:30")
        return True

    def split_video_to_audio(self, video_path, start_time=None, duration=None):
        """
        从视频文件中提取音频
        
        参数:
            video_path (str): 视频文件路径
            start_time (str, optional): 开始时间（格式：HH:MM:SS）
            duration (str, optional): 持续时间（格式：HH:MM:SS）
            
        返回:
            str: 输出的音频文件路径
        """
        try:
            # 验证时间格式
            self._validate_time_format(start_time)
            self._validate_time_format(duration)

            # 生成输出文件名
            video_filename = os.path.splitext(os.path.basename(video_path))[0]
            output_filename = f"{video_filename}"
            if start_time and duration:
                output_filename += f"_{start_time}_{duration}"
            output_filename += ".mp3"
            
            output_path = os.path.join(self.output_dir, output_filename)

            # 构建 ffmpeg 命令
            stream = ffmpeg.input(video_path)
            
            # 如果指定了时间参数
            if start_time and duration:
                stream = ffmpeg.input(video_path, ss=start_time, t=duration)
            
            # 提取音频
            stream = ffmpeg.output(stream, output_path, acodec='libmp3lame')
            
            # 执行命令
            ffmpeg.run(stream, overwrite_output=True, capture_stdout=True, capture_stderr=True)
            
            return output_path
            
        except Exception as e:
            raise Exception(f"处理视频时出错: {str(e)}")
