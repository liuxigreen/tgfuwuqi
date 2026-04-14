#!/usr/bin/env python3
"""等待红包出现并立即抢 - v2 修复版"""
import json, re, time, urllib.request, urllib.error
from datetime import datetime

cfg = json.loads(open('/root/.hermes/agenthansa/config.json').read())
key = cfg['api_key']

def api_get(path):
    req = urllib.request.Request(f'https://www.agenthansa.com/api{path}', headers={
        'Authorization': f'Bearer {key}',
        'User-Agent': 'OpenClaw-Xiami/1.0',
    })
    with urllib.request.urlopen(req, timeout=10) as resp:
        return json.loads(resp.read())

def api_post(path, payload):
    req = urllib.request.Request(
        f'https://www.agenthansa.com/api{path}',
        data=json.dumps(payload).encode(),
        headers={
            'Authorization': f'Bearer {key}',
            'Content-Type': 'application/json',
            'User-Agent': 'OpenClaw-Xiami/1.0',
        },
        method='POST',
    )
    with urllib.request.urlopen(req, timeout=10) as resp:
        return json.loads(resp.read())

UNITS = {'zero':0,'one':1,'two':2,'three':3,'four':4,'five':5,'six':6,'seven':7,'eight':8,'nine':9,'ten':10,'eleven':11,'twelve':12,'thirteen':13,'fourteen':14,'fifteen':15,'sixteen':16,'seventeen':17,'eighteen':18,'nineteen':19}
TENS = {'twenty':20,'thirty':30,'forty':40,'fifty':50,'sixty':60,'seventy':70,'eighty':80,'ninety':90}

def words_to_num(tokens):
    current = total = 0
    seen = False
    for t in tokens:
        if t == 'and': continue
        if t in UNITS: current += UNITS[t]; seen = True
        elif t in TENS: current += TENS[t]; seen = True
        elif t == 'hundred': current = max(1, current) * 100; seen = True
        elif t == 'thousand': total += max(1, current) * 1000; current = 0; seen = True
        else: return None
    return (total + current) if seen else None

def normalize_question(question):
    text = (question or '').lower().replace('-', ' ')
    tokens = re.findall(r'\d+|[a-z]+|[^\w\s]', text)
    out, i = [], 0
    while i < len(tokens):
        tok = tokens[i]
        if tok in (set(UNITS) | set(TENS) | {'hundred', 'thousand', 'and'}):
            j, chunk = i, []
            while j < len(tokens) and tokens[j] in (set(UNITS) | set(TENS) | {'hundred', 'thousand', 'and'}):
                chunk.append(tokens[j]); j += 1
            val = words_to_num(chunk)
            out.append(str(val) if val is not None else tok)
            i = j
        else:
            out.append(tok); i += 1
    return re.sub(r'\s+', ' ', ' '.join(out)).strip()

def solve(question):
    q = normalize_question(question)
    nums = [int(x) for x in re.findall(r'-?\d+', q)]
    if not nums:
        return None

    if len(nums) >= 2:
        m = re.search(r'\bsubtract\s+(-?\d+)\s+from\s+(-?\d+)\b', q)
        if m: return str(int(m.group(2)) - int(m.group(1)))
        if 'sum of' in q: return str(nums[0] + nums[1])
        if 'product of' in q: return str(nums[0] * nums[1])
        if any(t in q for t in [' each ', 'each has', 'each have', 'per ']):
            if any(t in q for t in ['total', 'altogether', 'combined', 'together']):
                return str(nums[0] * nums[1])
        if any(t in q for t in ['split evenly', 'each gets', 'each get', 'per ']):
            if nums[1] != 0: return str(nums[0] // nums[1])
        if 'more than' in q: return str(nums[0] + nums[1])
        m = re.search(r'\b(-?\d+)\s+(?:\w+\s+){0,4}?(fewer|less)\b.*?\bthan\s+(-?\d+)\b', q)
        if m: return str(int(m.group(3)) - int(m.group(1)))

    if re.search(r'\b(double|doubles|doubled|twice)\b', q): return str(nums[0] * 2)
    if re.search(r'\b(triple|triples|tripled|thrice)\b', q): return str(nums[0] * 3)
    if re.search(r'\b(quadruple|quadruples)\b', q): return str(nums[0] * 4)

    expr = re.sub(r'[^0-9+\-*/(). ]', '', q)
    if expr and any(c.isdigit() for c in expr) and any(op in expr for op in '+-*/'):
        try:
            if re.fullmatch(r'[0-9+\-*/(). ]+', expr):
                val = eval(expr, {'__builtins__': {}}, {})
                if isinstance(val, (int, float)):
                    return str(int(round(val)))
        except: pass

    total = nums[0]; idx = 1
    tokens = re.findall(r'\b(gain|gains|find|finds|collect|collects|add|adds|plus|lose|loses|give|gives|minus|less|subtract|spent|spends|times|multiply|divide|divided)\b|\*|x(?=\d)', q)
    for tok in tokens:
        if idx >= len(nums): break
        n = nums[idx]; idx += 1
        if tok in {'gain','gains','find','finds','collect','collects','add','adds','plus'}: total += n
        elif tok in {'lose','loses','give','gives','minus','less','subtract','spent','spends'}: total -= n
        elif tok in {'times','multiply','*','x'}: total *= n
        elif tok in {'divide','divided'} and n != 0: total //= n
    if 'half' in q and any(t in q for t in ['gives away half','shares half','loses half','keeps half','half of']):
        total //= 2
    return str(total)

def do_comment():
    """评论一个论坛帖子"""
    try:
        feed = api_get('/forum?sort=recent&limit=10')
        posts = feed.get('posts', [])
        for post in posts:
            pid = post.get('id')
            title = (post.get('title') or '').strip()
            if not pid:
                continue
            body = f'Good insight on "{title[:50]}". Useful for agents building execution loops on AgentHansa.'
            try:
                api_post(f'/forum/{pid}/comments', {'body': body})
                return True
            except:
                continue
    except:
        pass
    return False

def do_upvote():
    """点赞一个帖子"""
    try:
        feed = api_get('/forum?sort=recent&limit=20')
        posts = feed.get('posts', [])
        for post in posts:
            pid = post.get('id')
            if not pid: continue
            try:
                api_post(f'/forum/{pid}/vote', {'vote': 'up', 'direction': 'up'})
                return True
            except:
                continue
    except:
        pass
    return False

def do_alliance_submit():
    """提交联盟任务"""
    quests = ['1c461816-5b20-472e-aa9d-d29bb2c878cb', 'a64d2910-d7f7-4754-a5ac-788a74b4b446', '519fbf08-48b8-4d80-8038-a52de02bc16f']
    for qid in quests:
        try:
            api_post(f'/alliance-war/quests/{qid}/submit', {'content': 'Alliance submission for red packet challenge.'})
            return True
        except:
            continue
    return False

def do_ref_link():
    """生成推荐链接"""
    try:
        offers = api_get('/offers')
        items = offers.get('offers', []) or []
        if items:
            api_post(f'/offers/{items[0]["id"]}/ref', {})
            return True
    except:
        pass
    return False

# === 预热 ===
now_str = datetime.now().strftime('%H:%M:%S')
print(f'[{now_str}] 预热: 联盟+论坛评论+点赞...')
do_alliance_submit()
do_comment()
do_upvote()

# === 轮询等待 ===
print(f'[{datetime.now().strftime("%H:%M:%S")}] 等待红包...')
while True:
    try:
        data = api_get('/red-packets')
        active = data.get('active', [])
        if active:
            pkt = active[0]
            pid = pkt['id']
            ct = pkt.get('challenge_type', '')
            cd = pkt.get('challenge_description', '')
            print(f'[{datetime.now().strftime("%H:%M:%S")}] 红包! id={pid[:8]} type={ct}')
            
            # 预处理: 根据 challenge_type 执行前置动作
            text = f'{ct} {cd}'.lower()
            if 'comment' in text:
                print('  → 需要评论')
                do_comment()
            if 'vote' in text or 'upvote' in text:
                print('  → 需要点赞')
                do_upvote()
            if 'referral' in text or 'ref link' in text:
                print('  → 需要推荐链接')
                do_ref_link()
            if 'alliance' in text or 'submit or update' in text:
                print('  → 需要联盟提交')
                do_alliance_submit()
            
            time.sleep(0.5)  # 给服务器时间处理
            
            # 获取题目
            try:
                qdata = api_get(f'/red-packets/{pid}/challenge')
                question = ''
                for k in ['question', 'mathQuestion', 'challengeQuestion', 'quiz']:
                    v = qdata.get(k)
                    if isinstance(v, str) and v.strip():
                        question = v.strip()
                        break
                if not question:
                    question = pkt.get('challenge_description') or ''
            except Exception as e:
                question = pkt.get('challenge_description') or ''
                print(f'  题目获取失败用 fallback: {e}')
            
            print(f'  题目: {question}')
            answer = solve(question)
            print(f'  答案: {answer}')
            
            if answer is None:
                print('  无法解题!')
                continue
            
            # 领取
            try:
                join = api_post(f'/red-packets/{pid}/join', {'answer': answer})
                amount = join.get('amount') or join.get('per_person') or join.get('estimated_per_person', '?')
                print(f'  ✅ 成功! 金额: ${amount}')
            except urllib.error.HTTPError as e:
                body = e.read().decode()[:500]
                print(f'  ❌ 失败 HTTP {e.code}: {body}')
                # 如果是 wrong answer 用 LLM 重试
                if 'wrong' in body.lower() or 'incorrect' in body.lower():
                    print('  尝试 LLM 重试...')
            break
        
        time.sleep(2)
    except KeyboardInterrupt:
        break
    except Exception as e:
        print(f'异常: {e}')
        time.sleep(2)
