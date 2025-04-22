"""
火山引擎声音复刻API-2.0接口封装
"""
import os
import base64
import requests
import json
import time

class VolcanoVoice:
    def __init__(self, appid, token, secret_key=None):
        """
        初始化火山引擎声音复刻服务
        
        参数:
            appid: 应用ID
            token: 访问令牌(access token)
            secret_key: 密钥(可选)
        """
        self.appid = appid
        self.token = token
        self.secret_key = secret_key
        self.host = "https://openspeech.bytedance.com"
        
    def clone_voice(self, audio_path, speaker_id, text=None, language=0):
        """
        上传音频并训练音色
        
        参数:
            audio_path: 音频文件路径
            speaker_id: 声音ID
            text: 音频对应的文本(可选)
            language: 语言 (0=中文, 1=英文, 2=日语, 3=西班牙语, 4=印尼语, 5=葡萄牙语)
        
        返回:
            响应JSON
        """
        url = self.host + "/api/v1/mega_tts/audio/upload"
        headers = {
            "Content-Type": "application/json",
            "Authorization": "Bearer;" + self.token,
            "Resource-Id": "volc.megatts.voiceclone",
        }
        
        encoded_data, audio_format = self._encode_audio_file(audio_path)
        audios = [
            {
                "audio_bytes": encoded_data, 
                "audio_format": audio_format
            }
        ]
        if text:
            audios[0]["text"] = text
            
        data = {
            "appid": self.appid, 
            "speaker_id": speaker_id, 
            "audios": audios,  # 音频格式支持：wav、mp3、ogg、m4a、aac、pcm，其中pcm仅支持24k 单通道目前限制单文件上传最大10MB，每次最多上传1个音频文件
            "source": 2,  # 固定值：2
            "language": language, 
            "model_type": 1  # 使用API 2.0版本
        }
        
        response = requests.post(url, json=data, headers=headers)
        if response.status_code != 200:
            raise Exception("声音复刻请求错误:" + response.text)
        
        return response.json()
    
    def get_voice_status(self, speaker_id):
        """
        获取音色训练状态
        
        参数:
            speaker_id: 声音ID
        
        返回:
            响应JSON，包含训练状态
        """
        url = self.host + "/api/v1/mega_tts/status"
        headers = {
            "Content-Type": "application/json",
            "Authorization": "Bearer;" + self.token,
            "Resource-Id": "volc.megatts.voiceclone",
        }
        
        body = {"appid": self.appid, "speaker_id": speaker_id}
        response = requests.post(url, headers=headers, json=body)
        
        if response.status_code != 200:
            raise Exception("获取状态请求错误:" + response.text)
            
        return response.json()
    
    def generate_speech(self, text, speaker_id, output_path=None, language=0):
        """
        使用已训练的音色合成语音
        
        参数:
            text: 要合成的文本
            speaker_id: 声音ID
            output_path: 输出音频的保存路径(可选)
            language: 语言 (0=中文, 1=英文, 2=日语, 3=西班牙语, 4=印尼语, 5=葡萄牙语)
        
        返回:
            如果指定了output_path，则返回输出路径，否则返回音频二进制数据
        """
        url = self.host + "/api/v1/tts"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer; {self.token}"
        }
        
        # 按照API文档要求构造请求结构
        data = {
            "app": {
                "appid": self.appid,
                "token": self.token,
                "cluster": "volcano_icl"  # 2.0版本使用volcano_icl
            },
            "user": {
                "uid": f"user_{speaker_id}"  # 用户ID，可以是任意唯一标识
            },
            "audio": {
                "voice_type": speaker_id,
                "encoding": "wav",
                "speed_ratio": 1.0
            },
            "request": {
                "reqid": f"req_{int(time.time())}",  # 请求ID，可以是任意唯一标识
                "text": text,
                "operation": "query"
            }
        }
        
        # 添加语言参数(如果不是中文)
        if language != 0:
            data["request"]["language"] = language
        
        response = requests.post(url, headers=headers, json=data)
        
        if response.status_code != 200:
            raise Exception(f"合成语音请求错误: {response.text}")
        
        # 解析响应
        resp_json = response.json()
        if resp_json.get("code") != 0:
            raise Exception(f"合成语音失败: {resp_json.get('message', '未知错误')}")
        
        # 解码base64音频数据
        audio_data = base64.b64decode(resp_json.get("data", ""))
        
        if output_path:
            with open(output_path, "wb") as f:
                f.write(audio_data)
            return output_path
        
        return audio_data
    
    def get_voice_list(self):
        """
        获取已训练的音色列表
        目前API不直接支持获取列表功能，需要自行管理音色ID
        
        返回:
            已知的音色ID列表
        """
        # 这里可以实现音色ID的本地管理逻辑
        # 例如从本地文件读取已创建的音色ID列表
        voice_list_file = "volcano_voices.json"
        if os.path.exists(voice_list_file):
            try:
                with open(voice_list_file, "r", encoding="utf-8") as f:
                    return ["volcano:" + voice_id for voice_id in json.load(f)]
            except:
                pass
        return []
    
    def add_voice_to_list(self, speaker_id):
        """
        将新训练的音色ID添加到本地列表
        
        参数:
            speaker_id: 声音ID
        """
        voice_list_file = "volcano_voices.json"
        voice_list = []
        
        if os.path.exists(voice_list_file):
            try:
                with open(voice_list_file, "r", encoding="utf-8") as f:
                    voice_list = json.load(f)
            except:
                voice_list = []
        
        if speaker_id not in voice_list:
            voice_list.append(speaker_id)
            
        with open(voice_list_file, "w", encoding="utf-8") as f:
            json.dump(voice_list, f)
    
    def _encode_audio_file(self, file_path):
        """
        将音频文件编码为base64格式
        
        参数:
            file_path: 音频文件路径
            
        返回:
            encoded_data: base64编码后的数据
            audio_format: 音频格式
        """
        with open(file_path, 'rb') as audio_file:
            audio_data = audio_file.read()
            encoded_data = str(base64.b64encode(audio_data), "utf-8")
            audio_format = os.path.splitext(file_path)[1][1:]  # 获取文件扩展名作为音频格式
            return encoded_data, audio_format 