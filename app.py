import gradio as gr
import os
import re
from dotenv import load_dotenv
from voice_clone import VoiceClone
from voice2text import AudioTranscriber
from split_vedio2audio import VideoAudioSplitter
from voice_generate import VoiceGenerator
import sys

# 检查.env文件是否存在
if not os.path.exists('.env'):
    print("\n错误：缺少 .env 文件！")
    print("请按照以下步骤设置：")
    print("1. 复制 .env.example 文件并重命名为 .env")
    print("2. 在 .env 文件中设置您的 SILICONFLOW_API_KEY")
    print("3. 重新运行程序\n")
    sys.exit(1)

# 加载环境变量
load_dotenv()

# 检查必要的环境变量
SILICONFLOW_API_KEY = os.getenv("SILICONFLOW_API_KEY")
if not SILICONFLOW_API_KEY:
    print("\n错误：SILICONFLOW_API_KEY 未设置！")
    print("请在 .env 文件中设置有效的 SILICONFLOW_API_KEY")
    print("如果您还没有 API 密钥，请联系管理员获取\n")
    sys.exit(1)

# 初始化服务
voice_clone = VoiceClone(SILICONFLOW_API_KEY)
transcriber = AudioTranscriber(SILICONFLOW_API_KEY)
video_splitter = VideoAudioSplitter()
voice_generator = VoiceGenerator(SILICONFLOW_API_KEY)

# 定义可用的模型
AVAILABLE_MODELS = {
    "CosyVoice2": "FunAudioLLM/CosyVoice2-0.5B",
    "Fish Speech": "fishaudio/fish-speech-1.5",
    "GPT-SoVITS": "RVC-Boss/GPT-SoVITS"
}

# 定义内置声音
built_in_voices = ["alex", "anna", "bella", "benjamin", "charles", "claire", "david", "diana"]

def validate_voice_id(voice_id):
    """验证克隆音色ID是否符合要求"""
    if not voice_id:
        return False, "音色ID不能为空"
    if len(voice_id) > 64:
        return False, "音色ID长度不能超过64个字符"
    if not re.match(r'^[a-zA-Z0-9_-]+$', voice_id):
        return False, "音色ID只能包含字母、数字、下划线和连字符"
    return True, "验证通过"

def process_voice_clone(audio_file, reference_text, target_text, model_choice, voice_id):
    """处理语音克隆请求"""
    if not audio_file or not reference_text or not target_text:
        return "请确保所有必填字段都已填写", None

    # 验证voice_id
    is_valid, message = validate_voice_id(voice_id)
    if not is_valid:
        return message, None

    try:
        # 上传参考音频
        model_id = AVAILABLE_MODELS[model_choice]
        print(f"上传语音文件: {audio_file}")
        result = voice_clone.upload_voice_base64(
            audio_file,
            voice_id,
            model_id,
            reference_text
        )

        if not result or 'uri' not in result:
            return "上传音频失败", None

        voice_uri = result['uri']

        # 生成输出音频文件路径
        output_dir = os.path.join("outputs", model_choice)
        os.makedirs(output_dir, exist_ok=True)
        output_path = os.path.join(output_dir, f"output_{voice_id}.wav")

        # 生成克隆语音
        voice_clone.speech(
            target_text,
            voice=voice_uri,
            model_id=model_id,
            speech_file_path=output_path
        )

        return "语音克隆成功完成！", output_path

    except Exception as e:
        return f"处理过程中出错: {str(e)}", None

def transcribe_audio(audio_file):
    """处理语音转文字请求"""
    if not audio_file:
        return "请上传音频文件"

    try:
        print(audio_file)  # audio_file is already a path string
        result = transcriber.transcriptions(audio_file)
        return result.get('text', '转写失败')
    except Exception as e:
        return f"转写过程中出错: {str(e)}"

def split_video_audio(video_file, start_time=None, duration=None):
    """处理视频分离音频请求"""
    if not video_file:
        return "请上传视频文件", None

    try:
        # 处理视频分离
        output_path = video_splitter.split_video_to_audio(
            video_file,
            start_time,
            duration
        )
        return "音频提取成功！", output_path
    except Exception as e:
        return f"处理过程中出错: {str(e)}", None

def generate_speech(text, model_choice, voice, speed, gain, response_format, sample_rate):
    """处理语音合成请求"""
    if not text:
        return "请输入要合成的文本", None
    
    try:
        # 生成输出音频文件路径
        output_dir = "outputs/generated"
        os.makedirs(output_dir, exist_ok=True)
        output_path = os.path.join(output_dir, f"generated_{os.urandom(4).hex()}.wav")
        
        # 生成语音
        model_id = AVAILABLE_MODELS[model_choice]
        speech_data = voice_generator.create_speech(
            text,
            model=model_id,
            voice=voice,
            speed=speed,
            gain=gain,
            response_format=response_format,
            sample_rate=sample_rate
        )
        
        # 保存音频文件
        with open(output_path, "wb") as f:
            f.write(speech_data)
            
        return "语音合成成功！", output_path
    except Exception as e:
        return f"处理过程中出错: {str(e)}", None

def refresh_voice_list():
    """刷新语音列表"""
    return gr.Dropdown(choices=voice_generator.get_voice_list())

def delete_voice(voice):
    """删除语音"""
    if not voice:
        return "请选择要删除的语音", None
    
    try:
        voice_uri = voice.split(':', 1)[-1]
        result = voice_generator.delete_voice(voice_uri)
        print("删除结果：", result)
        if result == "success":
            return "语音删除成功！", gr.Dropdown(choices=voice_generator.get_voice_list())
        else:
            return f"删除失败：{result.get('message', '未知错误')}", None
    except Exception as e:
        return f"删除过程中出错: {str(e)}", None

def process_voice_clone_and_refresh(audio_file, reference_text, target_text, model_choice, voice_id):
    """处理语音克隆并刷新音色列表"""
    status, audio = process_voice_clone(audio_file, reference_text, target_text, model_choice, voice_id)
    # 无论成功与否都刷新列表，因为可能有其他用户添加了新音色
    return status, audio, gr.Dropdown(choices=built_in_voices + voice_generator.get_voice_list())

# 创建 Gradio 界面
with gr.Blocks(title="数字人工具包") as demo:
    gr.Markdown("# 🎤 数字人工具包")

    with gr.Tabs():
        # 视频分离音频标签页
        with gr.Tab("视频分离音频"):
            gr.Markdown("### 视频分离音频\n\n* 将 mp4 格式的视频文件转成音频文件，支持视频文件的开始时间、持续时间分离音频\n* 使用ffmpeg分离音频：ffmpeg -ss 开始时间 -t 持续时间 -i 视频文件 -code:a copy 提取的音频文件")
            with gr.Row():
                with gr.Column():
                    video_input = gr.Video(label="上传视频文件")
                    start_time = gr.Textbox(
                        label="开始时间（格式：HH:MM:SS，例如 00:00:00）",
                        value="00:00:00",
                        placeholder="00:00:00"
                    )
                    duration = gr.Textbox(
                        label="持续时间（格式：HH:MM:SS，例如 00:00:30）",
                        value="00:00:30",
                        placeholder="00:00:00"
                    )
                    split_btn = gr.Button("开始分离", variant="primary")

                with gr.Column():
                    split_status = gr.Textbox(label="处理状态")
                    output_audio_file = gr.Audio(label="提取的音频")
                    send_to_clone_btn = gr.Button("发送到语音克隆", variant="secondary")

        # 语音转写标签页
        with gr.Tab("语音转写"):
            gr.Markdown("### 语音转写\n\n* 选择模型：FunAudioLLM/SenseVoiceSmall")
            audio_input_transcribe = gr.Audio(label="上传要转写的音频", type="filepath")
            transcribe_btn = gr.Button("开始转写", variant="primary")
            transcription_output = gr.Textbox(label="转写结果")
            
        # 语音克隆标签页
        with gr.Tab("语音克隆"):
            gr.Markdown("### 语音克隆")
            
            with gr.Tabs():
                # 上传音色部分
                with gr.TabItem("上传音色"):
                    gr.Markdown("#### 上传音色\n\n* 上传音频以及对应的转录文本，生成克隆音色")
                    with gr.Row():
                        with gr.Column():
                            audio_input = gr.Audio(label="上传参考音频", type="filepath")
                            with gr.Row():
                                reference_text = gr.Textbox(label="参考音频文本", placeholder="请输入参考音频对应的文本内容（可点击旁边的【转写音频】按钮后编辑）", scale=4)
                                transcribe_ref_btn = gr.Button("转写音频", scale=1, variant="primary")
                            model_choice = gr.Dropdown(
                                choices=list(AVAILABLE_MODELS.keys()),
                                label="选择模型",
                                value="CosyVoice2"
                            )
                            voice_id = gr.Textbox(
                                label="克隆音色ID（用户可以自己定义，只支持字母、数字、下划线和连字符，不超过64个字符）",
                                value="voice_" + os.urandom(4).hex(),
                                placeholder="请输入唯一的声音ID"
                            )
                            upload_btn = gr.Button("上传音色", variant="primary")

                        with gr.Column():
                            upload_status = gr.Textbox(label="上传状态")
                            with gr.Row():
                                refresh_clone_list_btn = gr.Button("🔄 刷新音色列表", variant="secondary")
                                delete_clone_btn = gr.Button("🗑️ 删除音色", variant="primary")
                            voice_list = gr.Dropdown(
                                choices=voice_generator.get_voice_list(),
                                label="已上传的音色列表",
                                interactive=True
                            )
                            voice_manage_status = gr.Textbox(label="音色管理状态", visible=True)
                
                # 克隆语音部分
                with gr.TabItem("克隆语音"):
                    gr.Markdown("#### 克隆语音\n\n* 根据已上传的音色生成语音")
                    with gr.Row():
                        with gr.Column():
                            clone_text = gr.Textbox(
                                label="要生成的文本",
                                placeholder="请输入要生成的文本内容",
                                lines=5
                            )
                            clone_model_select = gr.Dropdown(
                                choices=list(AVAILABLE_MODELS.keys()),
                                label="选择模型",
                                interactive=True,
                                value="CosyVoice2"
                            )
                            clone_voice_select = gr.Dropdown(
                                choices=voice_generator.get_voice_list(),
                                label="选择音色（从已上传的音色中选择）",
                                interactive=True
                            )
                            with gr.Row():
                                refresh_voice_btn = gr.Button("🔄 刷新音色列表", variant="secondary")
                            
                            with gr.Row():
                                clone_speed_slider = gr.Slider(
                                    minimum=0.25,
                                    maximum=4.0,
                                    value=1.0,
                                    step=0.1,
                                    label="语速"
                                )
                                clone_gain_slider = gr.Slider(
                                    minimum=-20,
                                    maximum=20,
                                    value=0,
                                    step=1,
                                    label="音量增益"
                                )
                            clone_btn = gr.Button("开始生成", variant="primary")

                        with gr.Column():
                            clone_status = gr.Textbox(label="生成状态")
                            cloned_audio = gr.Audio(label="生成的音频")

        # 语音合成标签页
        with gr.Tab("语音合成"):
            gr.Markdown("### 语音合成\n\n* 使用内置音色：alex, anna, bella, benjamin, charles, claire, david, diana\n* 根据选择的默认音色，将文字转换为音频")
            with gr.Row():
                with gr.Column():
                    text_input = gr.Textbox(
                        label="输入文本",
                        placeholder="请输入要合成的文本内容",
                        lines=5
                    )
                    model_select = gr.Dropdown(
                        choices=list(AVAILABLE_MODELS.keys()),
                        label="选择模型",
                        interactive=True,
                        value="CosyVoice2"
                    )
                    default_voice_select = gr.Dropdown(
                        choices=built_in_voices,
                        label="选择音色",
                        interactive=True,
                        value=built_in_voices[0]
                    )
                    with gr.Row():
                        response_format = gr.Dropdown(
                            choices=["mp3", "opus", "wav", "pcm"],
                            label="输出格式",
                            value="wav"
                        )
                        sample_rate = gr.Dropdown(
                            choices=[8000, 16000, 24000, 32000, 44100, 48000],
                            info="opus: Supports 48000 Hz. wav, pcm: Supports 8000, 16000, 24000, 32000, 44100 Hz, with a default of 44100 Hz. mp3: Supports 32000, 44100 Hz, with a default of 44100 Hz.",
                            label="采样率",
                            value=44100
                        )
                        speed_slider = gr.Slider(
                            minimum=0.25,
                            maximum=4.0,
                            value=1.0,
                            step=0.1,
                            label="语速"
                        )
                        gain_slider = gr.Slider(
                            minimum=-20,
                            maximum=20,
                            value=0,
                            step=1,
                            label="音量增益"
                        )
                    generate_btn = gr.Button("开始合成", variant="primary")

                with gr.Column():
                    generate_status = gr.Textbox(label="处理状态")
                    generated_audio = gr.Audio(label="合成的音频")

    # 绑定事件
    def send_to_voice_clone(audio):
        """将音频发送到语音克隆标签页"""
        if audio is None:
            return None
        return audio

    send_to_clone_btn.click(
        send_to_voice_clone,
        inputs=[output_audio_file],
        outputs=[audio_input]
    )

    transcribe_ref_btn.click(
        transcribe_audio,
        inputs=[audio_input],
        outputs=[reference_text]
    )

    # 定义刷新音色列表函数
    def refresh_clone_voice_list():
        return gr.Dropdown(choices=voice_generator.get_voice_list())

    # 定义删除并刷新音色的函数
    def delete_and_refresh_voice(voice):
        if not voice:
            return "请选择要删除的音色！", gr.Dropdown(choices=voice_generator.get_voice_list())
        status, _ = delete_voice(voice)
        return status, gr.Dropdown(choices=voice_generator.get_voice_list())

    # 定义上传音色功能
    def upload_voice(audio_file, reference_text, model_choice, voice_id):
        if not audio_file or not reference_text:
            return "请确保音频文件和参考文本都已填写", gr.Dropdown(choices=voice_generator.get_voice_list())

        # 验证voice_id
        is_valid, message = validate_voice_id(voice_id)
        if not is_valid:
            return message, gr.Dropdown(choices=voice_generator.get_voice_list())

        try:
            # 上传参考音频
            model_id = AVAILABLE_MODELS[model_choice]
            print(f"上传语音文件: {audio_file}")
            result = voice_clone.upload_voice_base64(
                audio_file,
                voice_id,
                model_id,
                reference_text
            )

            if not result or 'uri' not in result:
                return "上传音频失败", gr.Dropdown(choices=voice_generator.get_voice_list())

            return "音色上传成功！", gr.Dropdown(choices=voice_generator.get_voice_list())

        except Exception as e:
            return f"处理过程中出错: {str(e)}", gr.Dropdown(choices=voice_generator.get_voice_list())

    # 定义克隆语音功能
    def clone_voice(text, model_choice, voice, speed, gain):
        if not text or not voice:
            return "请确保文本和音色都已填写", None
        
        try:
            # 生成输出音频文件路径
            output_dir = "outputs/cloned"
            os.makedirs(output_dir, exist_ok=True)
            output_path = os.path.join(output_dir, f"cloned_{os.urandom(4).hex()}.wav")
            
            # 获取音色URI
            voice_uri = voice.split(':', 1)[-1]
            model_id = AVAILABLE_MODELS[model_choice]
            
            # 生成克隆语音
            voice_clone.speech(
                text,
                voice=voice_uri,
                model_id=model_id,
                speech_file_path=output_path
            )
            
            return "语音生成成功！", output_path
        except Exception as e:
            return f"处理过程中出错: {str(e)}", None

    # 绑定上传音色相关事件
    upload_btn.click(
        upload_voice,
        inputs=[audio_input, reference_text, model_choice, voice_id],
        outputs=[upload_status, voice_list]
    )
    
    refresh_clone_list_btn.click(
        refresh_clone_voice_list,
        outputs=[voice_list]
    )
    
    delete_clone_btn.click(
        delete_and_refresh_voice,
        inputs=[voice_list],
        outputs=[voice_manage_status, voice_list]
    )
    
    # 绑定克隆语音相关事件
    refresh_voice_btn.click(
        refresh_clone_voice_list,
        outputs=[clone_voice_select]
    )
    
    clone_btn.click(
        clone_voice,
        inputs=[clone_text, clone_model_select, clone_voice_select, clone_speed_slider, clone_gain_slider],
        outputs=[clone_status, cloned_audio]
    )
    
    transcribe_ref_btn.click(
        transcribe_audio,
        inputs=[audio_input],
        outputs=[reference_text]
    )

    transcribe_btn.click(
        transcribe_audio,
        inputs=[audio_input_transcribe],
        outputs=[transcription_output]
    )

    split_btn.click(
        split_video_audio,
        inputs=[video_input, start_time, duration],
        outputs=[split_status, output_audio_file]
    )

    generate_btn.click(
        generate_speech,
        inputs=[text_input, model_select, default_voice_select, speed_slider, gain_slider, response_format, sample_rate],
        outputs=[generate_status, generated_audio]
    )

if __name__ == "__main__":
    demo.launch(share=True)
