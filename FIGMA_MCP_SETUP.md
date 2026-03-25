# Figma MCP — Claude Code 연결 설치 가이드

다른 컴퓨터에서 Claude Code + Figma DevMode MCP를 연결할 때 아래 명령어를 순서대로 실행하세요.

---

## 1단계: 저장소 클론 & 빌드

```bash
cd ~
git clone https://github.com/steveaimkt/figma-mcp.git
cd figma-mcp
npm install
npm run build
```

---

## 2단계: Claude Code에 MCP 서버 등록

```bash
claude mcp add figma-write node "$(pwd)/dist/talk_to_figma_mcp/server.js"
```

> **특정 프로젝트에만 등록하려면** 프로젝트 폴더에 `.mcp.json` 파일 생성:
>
> ```json
> {
>   "mcpServers": {
>     "figma-write": {
>       "command": "node",
>       "args": ["/Users/YOUR_USERNAME/figma-mcp/dist/talk_to_figma_mcp/server.js"]
>     }
>   }
> }
> ```

---

## 3단계: Figma 플러그인 설치

Figma 앱에서 아래 플러그인을 설치하세요:

- **Figma → Plugins → Manage Plugins → Browse plugins**
- `Talk to Figma` 검색 후 설치

---

## 4단계: 등록 확인

```bash
# Claude Code 재시작 후
claude mcp list
```

`figma-write` 가 목록에 표시되면 성공입니다.

---

## 매번 사용할 때

1. Figma에서 **Talk to Figma 플러그인** 실행
2. 플러그인에서 생성된 **채널 코드** 복사
3. Claude에게 채널 코드 전달 → 연결 완료

---

## Figma 토큰 → Tailwind 추출 예시 프롬프트

Claude에게 아래와 같이 요청하세요:

```
채널코드: XXXXXX
Figma DevMode MCP 연결하고 선택한 프레임의 Color/Typography 변수들을
tailwind.config.js와 theme.css에 변수로 정의해줘. theme.js도 업데이트해줘.
```
