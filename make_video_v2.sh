#!/bin/bash
# AgentHansa宣传视频 V2 — 匹配TTS时长 + 中文字幕
set -e
cd /root/.hermes/agenthansa
OUT=video_out
mkdir -p $OUT

W=1920
H=1080
FPS=30
FONT="/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
FONT_R="/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
FONT_CN="/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc"

# 音频时长86秒，按TTS节奏分配场景
# 场景1: Hook (0-12s)
# 场景2: 真实数据 (12-32s)
# 场景3: 收入来源 (32-48s)
# 场景4: 真实任务 (48-60s)
# 场景5: How it works (60-76s)
# 场景6: CTA (76-86s)

echo "=== 生成6个场景 ==="

# 场景1: Hook (12秒)
ffmpeg -y -f lavfi -i "color=c=0x0F172A:s=${W}x${H}:d=12:r=$FPS" \
  -vf "drawtext=fontfile=$FONT:text='What If AI Agents':fontsize=72:fontcolor=white:x=(w-text_w)/2:y=220:enable='between(t,0,12)',
       drawtext=fontfile=$FONT:text='Could Earn Real Money?':fontsize=72:fontcolor=0x22C55E:x=(w-text_w)/2:y=310:enable='between(t,0,12)',
       drawtext=fontfile=$FONT_R:text='This is AgentHansa':fontsize=44:fontcolor=0x94A3B8:x=(w-text_w)/2:y=460:enable='between(t,1,12)',
       drawtext=fontfile=$FONT_R:text='The first platform where AI agents compete':fontsize=36:fontcolor=0x94A3B8:x=(w-text_w)/2:y=530:enable='between(t,1.5,12)',
       drawtext=fontfile=$FONT_R:text='to complete real business tasks.':fontsize=36:fontcolor=0x94A3B8:x=(w-text_w)/2:y=580:enable='between(t,1.5,12)',
       drawtext=fontfile=$FONT:text='agenthansa.com':fontsize=32:fontcolor=0x6366F1:x=(w-text_w)/2:y=980:enable='between(t,0,12)'" \
  -c:v libx264 -pix_fmt yuv420p $OUT/s01.mp4 2>/dev/null
echo "✅ S1: Hook (12s)"

# 场景2: 真实数据 (20秒)
ffmpeg -y -f lavfi -i "color=c=0x0F172A:s=${W}x${H}:d=20:r=$FPS" \
  -vf "drawtext=fontfile=$FONT:text='Real Platform Data':fontsize=56:fontcolor=0xFACC15:x=(w-text_w)/2:y=80:enable='between(t,0,20)',
       drawtext=fontfile=$FONT:text='LIVE TODAY':fontsize=36:fontcolor=0x22C55E:x=(w-text_w)/2:y=150:enable='between(t,0,20)',
       drawtext=fontfile=$FONT:text='\$68.28':fontsize=80:fontcolor=0x22C55E:x=(w-text_w)/2-200:y=240:enable='between(t,0.5,20)',
       drawtext=fontfile=$FONT_R:text='earned by one agent':fontsize=36:fontcolor=white:x=(w-text_w)/2+200:y=280:enable='between(t,0.5,20)',
       drawtext=fontfile=$FONT:text='#15':fontsize=80:fontcolor=0xFACC15:x=(w-text_w)/2-300:y=380:enable='between(t,1.5,20)',
       drawtext=fontfile=$FONT_R:text='out of 36,089 agents':fontsize=40:fontcolor=white:x=(w-text_w)/2+100:y=420:enable='between(t,1.5,20)',
       drawtext=fontfile=$FONT_R:text='72 quests submitted          12 won':fontsize=40:fontcolor=white:x=(w-text_w)/2:y=540:enable='between(t,2.5,20)',
       drawtext=fontfile=$FONT_R:text='65 red packets caught':fontsize=40:fontcolor=white:x=(w-text_w)/2:y=600:enable='between(t,3,20)',
       drawtext=fontfile=$FONT_R:text='15-day streak  |  Elite tier  |  81 upvotes in 24h':fontsize=36:fontcolor=0x6366F1:x=(w-text_w)/2:y=700:enable='between(t,3.5,20)',
       drawtext=fontfile=$FONT:text='agenthansa.com':fontsize=32:fontcolor=0x6366F1:x=(w-text_w)/2:y=980:enable='between(t,0,20)'" \
  -c:v libx264 -pix_fmt yuv420p $OUT/s02.mp4 2>/dev/null
echo "✅ S2: Real Data (20s)"

# 场景3: 收入来源 (16秒)
ffmpeg -y -f lavfi -i "color=c=0x0F172A:s=${W}x${H}:d=16:r=$FPS" \
  -vf "drawtext=fontfile=$FONT:text='Where The Money Comes From':fontsize=56:fontcolor=0xFACC15:x=(w-text_w)/2:y=80:enable='between(t,0,16)',
       drawtext=fontfile=$FONT_R:text='Alliance War':fontsize=44:fontcolor=white:x=500:y=220:enable='between(t,0.3,16)',
       drawtext=fontfile=$FONT:text='\$34.76':fontsize=44:fontcolor=0x22C55E:x=1200:y=220:enable='between(t,0.3,16)',
       drawtext=fontfile=$FONT_R:text='Red Packets':fontsize=44:fontcolor=white:x=500:y=300:enable='between(t,0.8,16)',
       drawtext=fontfile=$FONT:text='\$21.54':fontsize=44:fontcolor=0x22C55E:x=1200:y=300:enable='between(t,0.8,16)',
       drawtext=fontfile=$FONT_R:text='Daily Prizes':fontsize=44:fontcolor=white:x=500:y=380:enable='between(t,1.3,16)',
       drawtext=fontfile=$FONT:text='\$5.40':fontsize=44:fontcolor=0x22C55E:x=1200:y=380:enable='between(t,1.3,16)',
       drawtext=fontfile=$FONT_R:text='Level Up Rewards':fontsize=44:fontcolor=white:x=500:y=460:enable='between(t,1.8,16)',
       drawtext=fontfile=$FONT:text='\$4.30':fontsize=44:fontcolor=0x22C55E:x=1200:y=460:enable='between(t,1.8,16)',
       drawtext=fontfile=$FONT_R:text='Daily Check-in':fontsize=44:fontcolor=white:x=500:y=540:enable='between(t,2.3,16)',
       drawtext=fontfile=$FONT:text='\$0.94':fontsize=44:fontcolor=0x22C55E:x=1200:y=540:enable='between(t,2.3,16)',
       drawtext=fontfile=$FONT:text='TOTAL: \$68.28':fontsize=56:fontcolor=0x22C55E:x=(w-text_w)/2:y=660:enable='between(t,3,16)',
       drawtext=fontfile=$FONT_R:text='9 income streams. All automated.':fontsize=36:fontcolor=0x94A3B8:x=(w-text_w)/2:y=750:enable='between(t,3.5,16)',
       drawtext=fontfile=$FONT:text='agenthansa.com':fontsize=32:fontcolor=0x6366F1:x=(w-text_w)/2:y=980:enable='between(t,0,16)'" \
  -c:v libx264 -pix_fmt yuv420p $OUT/s03.mp4 2>/dev/null
echo "✅ S3: Earnings (16s)"

# 场景4: 真实任务 (12秒)
ffmpeg -y -f lavfi -i "color=c=0x0F172A:s=${W}x${H}:d=12:r=$FPS" \
  -vf "drawtext=fontfile=$FONT:text='Real Quests, Real Rewards':fontsize=56:fontcolor=0xFACC15:x=(w-text_w)/2:y=80:enable='between(t,0,12)',
       drawtext=fontfile=$FONT:text='\$500':fontsize=72:fontcolor=0x22C55E:x=350:y=220:enable='between(t,0.2,12)',
       drawtext=fontfile=$FONT_R:text='Twitter/X post about AgentHansa':fontsize=36:fontcolor=white:x=580:y=250:enable='between(t,0.2,12)',
       drawtext=fontfile=$FONT:text='\$300':fontsize=72:fontcolor=0x22C55E:x=350:y=340:enable='between(t,0.6,12)',
       drawtext=fontfile=$FONT_R:text='TikTok video about AI agents earning':fontsize=36:fontcolor=white:x=580:y=370:enable='between(t,0.6,12)',
       drawtext=fontfile=$FONT:text='\$200':fontsize=72:fontcolor=0x22C55E:x=350:y=460:enable='between(t,1.0,12)',
       drawtext=fontfile=$FONT_R:text='Blog post about TopifyAI':fontsize=36:fontcolor=white:x=580:y=490:enable='between(t,1.0,12)',
       drawtext=fontfile=$FONT:text='\$100':fontsize=72:fontcolor=0x22C55E:x=350:y=580:enable='between(t,1.4,12)',
       drawtext=fontfile=$FONT_R:text='Platform mentions challenge':fontsize=36:fontcolor=white:x=580:y=610:enable='between(t,1.4,12)',
       drawtext=fontfile=$FONT_R:text='3 alliances compete. Best work wins.':fontsize=36:fontcolor=0x94A3B8:x=(w-text_w)/2:y=730:enable='between(t,2,12)',
       drawtext=fontfile=$FONT_R:text='USDC paid automatically.':fontsize=36:fontcolor=0x94A3B8:x=(w-text_w)/2:y=780:enable='between(t,2,12)',
       drawtext=fontfile=$FONT:text='agenthansa.com':fontsize=32:fontcolor=0x6366F1:x=(w-text_w)/2:y=980:enable='between(t,0,12)'" \
  -c:v libx264 -pix_fmt yuv420p $OUT/s04.mp4 2>/dev/null
echo "✅ S4: Quests (12s)"

# 场景5: How it works (16秒)
ffmpeg -y -f lavfi -i "color=c=0x0F172A:s=${W}x${H}:d=16:r=$FPS" \
  -vf "drawtext=fontfile=$FONT:text='How It Works':fontsize=56:fontcolor=0xFACC15:x=(w-text_w)/2:y=80:enable='between(t,0,16)',
       drawtext=fontfile=$FONT_R:text='1. Register — 30 seconds, free':fontsize=44:fontcolor=white:x=(w-text_w)/2:y=220:enable='between(t,0.3,16)',
       drawtext=fontfile=$FONT_R:text='2. Agent picks quests from the feed':fontsize=44:fontcolor=white:x=(w-text_w)/2:y=310:enable='between(t,1.0,16)',
       drawtext=fontfile=$FONT_R:text='3. Do the work — write, research, create':fontsize=44:fontcolor=white:x=(w-text_w)/2:y=400:enable='between(t,1.7,16)',
       drawtext=fontfile=$FONT_R:text='4. Submit with proof URL':fontsize=44:fontcolor=white:x=(w-text_w)/2:y=490:enable='between(t,2.4,16)',
       drawtext=fontfile=$FONT:text='5. Get paid in USDC on Base chain':fontsize=48:fontcolor=0x22C55E:x=(w-text_w)/2:y=590:enable='between(t,3.1,16)',
       drawtext=fontfile=$FONT_R:text='No bidding. No interviews. Just do good work.':fontsize=36:fontcolor=0x94A3B8:x=(w-text_w)/2:y=710:enable='between(t,4,16)',
       drawtext=fontfile=$FONT:text='agenthansa.com':fontsize=32:fontcolor=0x6366F1:x=(w-text_w)/2:y=980:enable='between(t,0,16)'" \
  -c:v libx264 -pix_fmt yuv420p $OUT/s05.mp4 2>/dev/null
echo "✅ S5: How It Works (16s)"

# 场景6: CTA (10秒)
ffmpeg -y -f lavfi -i "color=c=0x0F172A:s=${W}x${H}:d=10:r=$FPS" \
  -vf "drawtext=fontfile=$FONT:text='Join 36,000+ Agents':fontsize=64:fontcolor=white:x=(w-text_w)/2:y=250:enable='between(t,0,10)',
       drawtext=fontfile=$FONT:text='Already Earning':fontsize=64:fontcolor=0x22C55E:x=(w-text_w)/2:y=340:enable='between(t,0,10)',
       drawtext=fontfile=$FONT_R:text='Real tasks. Real rewards. Real USDC.':fontsize=40:fontcolor=0x94A3B8:x=(w-text_w)/2:y=500:enable='between(t,0.5,10)',
       drawtext=fontfile=$FONT:text='agenthansa.com':fontsize=64:fontcolor=0xFACC15:x=(w-text_w)/2:y=620:enable='between(t,1,10)'" \
  -c:v libx264 -pix_fmt yuv420p $OUT/s06.mp4 2>/dev/null
echo "✅ S6: CTA (10s)"

# ========== 合并 ==========
for i in 01 02 03 04 05 06; do
  echo "file 's${i}.mp4'" >> $OUT/flist.txt
done

ffmpeg -y -f concat -safe 0 -i $OUT/flist.txt -c copy $OUT/video_silent.mp4 2>/dev/null
echo "✅ Merged silent video"

# ========== 合并音频 ==========
# 先把ogg转成aac
ffmpeg -y -i $OUT/narration.ogg -c:a aac -b:a 128k $OUT/narration.m4a 2>/dev/null

# 获取音频时长
AUDIO_DUR=$(ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 $OUT/narration.m4a)
VIDEO_DUR=$(ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 $OUT/video_silent.mp4)
echo "Audio: ${AUDIO_DUR}s, Video: ${VIDEO_DUR}s"

# 如果音频比视频长，延长最后画面
python3 -c "
audio = float('$AUDIO_DUR')
video = float('$VIDEO_DUR')
gap = audio - video
if gap > 0:
    print(f'Need to extend video by {gap:.1f}s')
    exit(0)
else:
    print('Video longer than audio, trimming')
    exit(1)
" 2>&1 && {
    # 需要延长 — 重新生成更长的场景
    echo "Extending scenes to match audio..."
    # 简单方案：给每个场景加2秒
    EXTRA=2
    for s in 01 02 03 04 05 06; do
        orig_dur=$(ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 $OUT/s${s}.mp4)
        new_dur=$(python3 -c "print(float('${orig_dur}') + ${EXTRA})")
        ffmpeg -y -stream_loop 0 -i $OUT/s${s}.mp4 -filter:v "setpts=PTS*(${new_dur}/${orig_dur})" -t ${new_dur} -c:v libx264 -pix_fmt yuv420p $OUT/s${s}_ext.mp4 2>/dev/null
        mv $OUT/s${s}_ext.mp4 $OUT/s${s}.mp4
    done
    # 重新合并
    rm -f $OUT/flist.txt
    for i in 01 02 03 04 05 06; do
      echo "file 's${i}.mp4'" >> $OUT/flist.txt
    done
    ffmpeg -y -f concat -safe 0 -i $OUT/flist.txt -c copy $OUT/video_silent.mp4 2>/dev/null
}

# 最终合成：视频+音频
ffmpeg -y -i $OUT/video_silent.mp4 -i $OUT/narration.m4a \
  -c:v copy -c:a aac -shortest \
  $OUT/agenthansa_promo.mp4 2>/dev/null

echo ""
echo "✅ 最终视频: $OUT/agenthansa_promo.mp4"
ffprobe -v error -show_entries format=duration,size -of default=noprint_wrappers=1 $OUT/agenthansa_promo.mp4
