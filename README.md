# [README.md](https://github.com/user-attachments/files/23782865/README.md)
# Automated Deployment System
## n8n + Notion + Claude AI + GitHub Integration

---

## 📋 프로젝트 개요

### 목적
Notion을 중앙 제어판으로 사용하여 코드 수정 및 배포 워크플로우를 완전 자동화하는 시스템입니다. 사용자가 Notion 데이터베이스에서 코드 변경을 요청하면, Claude AI가 자동으로 GitHub 소스 파일을 분석하고, 요청된 변경사항을 적용하며, 전체 프로세스를 관리합니다.

### 핵심 가치
- **완전 자동화**: 코드 수정 요청부터 GitHub 배포까지 수동 개입 최소화
- **MCP(Master Control Program) 접근**: 엔터프라이즈급 신뢰성과 체계적인 오류 처리
- **상태 추적**: Notion을 통한 실시간 진행 상황 모니터링

---

## 🏗️ 시스템 아키텍처

### 기술 스택
- **워크플로우 엔진**: n8n
- **제어 패널**: Notion Database
- **AI 엔진**: Claude AI API
- **버전 관리**: GitHub API
- **인증**: 
  - Notion API Integration Token
  - GitHub Personal Access Token (repo 권한)
  - Claude API Key

### 워크플로우 구조

```
[Notion Database] 
    ↓ (상태 변경 감지)
[n8n Schedule Trigger]
    ↓
[수정 워크플로우] → [배포 워크플로우]
    ↓                    ↓
[Claude AI]         [GitHub API]
    ↓                    ↓
[Notion 업데이트]    [코드 커밋]
```

---

## 📊 Notion 데이터베이스 구조

### 필드 정의

| 필드명 | 타입 | 설명 |
|--------|------|------|
| **name** | Title | 수정 요청 이름 |
| **status** | Select | 현재 진행 상태 |
| **github-url** | URL | 대상 GitHub 파일 URL |
| **revisions** | Rich Text | 수정 지시사항 (상세) |
| **output** | Rich Text | Claude의 수정 결과물 |
| **commit** | Rich Text | GitHub 커밋 메시지 |

### 상태 시스템 (4단계)

1. **시작 전** - 초기 상태
2. **수정** - 코드 수정 트리거 (Workflow 1 실행)
3. **완료** - 수정 완료 (검토 단계)
4. **배포** - GitHub 배포 트리거 (Workflow 2 실행)

---

## 🔄 워크플로우 상세

### Workflow 1: 코드 수정 워크플로우
**트리거**: 상태가 "수정"으로 변경될 때

#### 노드 구성
1. **Schedule Trigger** (1분마다 실행)
2. **Notion Get Many** - 상태가 "수정"인 페이지 조회
3. **IF Node** - 데이터 존재 확인
4. **HTTP Request 1** - GitHub 파일 가져오기
   ```
   Method: GET
   URL: {{ $json.properties['github-url'].url }}
   Headers: 
     - Authorization: token YOUR_GITHUB_TOKEN
     - Accept: application/vnd.github.raw+json
   ```
5. **Code Node** - GitHub 응답 파싱
   ```javascript
   return [{
     json: {
       file_content: items[0].body,
       page_id: items[0].json.id,
       revisions: items[0].json.properties.revisions.rich_text[0].plain_text
     }
   }];
   ```
6. **HTTP Request 2** - Claude AI 호출
   ```json
   {
     "model": "claude-sonnet-4-20250514",
     "max_tokens": 4096,
     "messages": [
       {
         "role": "user",
         "content": "다음 코드를 수정해주세요:\n\n[원본 코드]\n\n수정 요청사항:\n[revisions]"
       }
     ]
   }
   ```
7. **Code Node** - Claude 응답 파싱
8. **HTTP Request 3** - Notion 업데이트
   - output 필드에 수정된 코드 저장
   - status를 "완료"로 변경

### Workflow 2: 배포 워크플로우
**트리거**: 상태가 "배포"로 변경될 때

#### 노드 구성
1. **Schedule Trigger** (1분마다 실행)
2. **Notion Get Many** - 상태가 "배포"인 페이지 조회
3. **IF Node** - 데이터 존재 확인
4. **Code Node** - GitHub API 요청 준비
   ```javascript
   const pageId = items[0].json.id;
   const outputContent = items[0].json.properties.output.rich_text[0].plain_text;
   const commitMessage = items[0].json.properties.commit.rich_text[0].plain_text;
   const githubUrl = items[0].json.properties['github-url'].url;
   
   // URL에서 owner, repo, path 추출
   const apiUrl = `https://api.github.com/repos/${owner}/${repo}/contents/${path}`;
   
   // Base64 인코딩
   const contentBase64 = Buffer.from(outputContent).toString('base64');
   
   return [{
     json: {
       page_id: pageId,
       api_url: apiUrl,
       content_base64: contentBase64,
       commit_message: commitMessage
     }
   }];
   ```
5. **HTTP Request** - GitHub 파일 업데이트 (PUT)
   ```json
   {
     "message": "{{ $json.commit_message }}",
     "content": "{{ $json.content_base64 }}"
   }
   ```
   **주요 발견**: SHA 값 없이 완전 덮어쓰기 가능!
6. **HTTP Request** - Notion 상태 업데이트
   - status를 "시작 전"으로 초기화

---

## 🎯 핵심 기술 해결 사항

### 1. GitHub API 단순화
**문제**: 파일 업데이트 시 SHA 값 필요성에 대한 혼란
**해결**: 완전 덮어쓰기 방식으로 SHA 값 없이도 업데이트 가능
- 기존 파일을 완전히 교체하는 경우 SHA 불필요
- API 호출 횟수 감소 (GET → PUT 대신 PUT만)

### 2. n8n 데이터 플로우
**문제**: 노드 간 데이터 전달 방식 이해 부족
**해결**: Notion 데이터 구조 이해
```javascript
// Notion 필드 참조 형식
$json.properties['field-name'].rich_text[0].plain_text
$json.properties['field-name'].url
$json.id // Page ID
```

### 3. Base64 인코딩
**문제**: GitHub API가 Base64 인코딩된 컨텐츠 요구
**해결**: Code Node에서 인코딩 처리
```javascript
const contentBase64 = Buffer.from(textContent).toString('base64');
```

### 4. 워크플로우 분리
**원칙**: 복잡한 단일 워크플로우보다 단순한 분리 워크플로우
- 수정 워크플로우와 배포 워크플로우 독립 실행
- 각 워크플로우는 하나의 상태 전환만 담당
- Loop Over Items 대신 한 번에 하나의 페이지 처리

---

## 🐛 디버깅 전략

### 체계적 접근법
1. **단계별 테스트**: 각 노드를 개별적으로 테스트
2. **상세 로깅**: 에러 발생 시 스크린샷과 정확한 에러 메시지 수집
3. **데이터 검증**: 각 노드의 출력 데이터 구조 확인
4. **단순화 우선**: 복잡한 로직보다 작동하는 단순한 구현 선호

### 일반적인 문제 해결

#### 문제: Notion 필드를 읽을 수 없음
```javascript
// ❌ 잘못된 방법
$json.properties.revisions

// ✅ 올바른 방법
$json.properties.revisions.rich_text[0].plain_text
```

#### 문제: GitHub API 인증 실패
```
Headers 확인:
- Authorization: token YOUR_TOKEN (Bearer 아님!)
- Accept: application/vnd.github.raw+json
```

#### 문제: n8n 워크플로우가 트리거되지 않음
- Schedule Trigger 간격 확인 (최소 1분)
- Notion 쿼리 필터 검증
- IF 노드 조건 로직 확인

---

## 📝 사용 가이드

### 초기 설정

1. **Notion 데이터베이스 생성**
   - 위 필드 정의에 따라 데이터베이스 구성
   - Integration 추가 및 API 토큰 발급

2. **GitHub 토큰 발급**
   - Settings → Developer settings → Personal access tokens
   - `repo` 권한 부여

3. **Claude API 키 발급**
   - Anthropic Console에서 API 키 생성

4. **n8n 워크플로우 가져오기**
   - Workflow 1 (수정) 가져오기
   - Workflow 2 (배포) 가져오기
   - 각 HTTP Request 노드에 토큰 설정

### 운영 프로세스

1. **코드 수정 요청**
   - Notion에 새 페이지 생성
   - 필수 필드 입력:
     - name: "기능명 수정"
     - github-url: 대상 파일 전체 URL
     - revisions: 구체적인 수정 지시사항
     - commit: 커밋 메시지
   - status를 "수정"으로 변경

2. **자동 처리 대기**
   - n8n이 1분 이내에 감지
   - Claude가 코드 분석 및 수정
   - output 필드에 결과 저장
   - status가 "완료"로 자동 변경

3. **검토 및 배포**
   - output 필드의 수정된 코드 검토
   - 문제 없으면 status를 "배포"로 변경
   - 자동으로 GitHub에 커밋
   - status가 "시작 전"으로 초기화

---

## 🔮 향후 개선 방향

### 단기 목표
- [ ] 에러 처리 강화 (Slack/이메일 알림)
- [ ] 다중 파일 동시 수정 지원
- [ ] 롤백 기능 추가

### 중기 목표
- [ ] 동적 GitHub 리포지토리 지원 (현재는 고정 경로)
- [ ] Pull Request 생성 옵션
- [ ] 테스트 자동화 통합

### 장기 목표
- [ ] 웹 UI 대시보드 개발
- [ ] AI 기반 코드 리뷰 자동화
- [ ] 다중 브랜치 전략 지원

---

## 📚 참고 자료

### API 문서
- [Notion API](https://developers.notion.com/)
- [GitHub REST API](https://docs.github.com/en/rest)
- [Claude API](https://docs.anthropic.com/)
- [n8n Documentation](https://docs.n8n.io/)

### 핵심 학습 포인트
1. **단순함의 힘**: 복잡한 워크플로우보다 여러 개의 단순한 워크플로우
2. **완전 덮어쓰기**: GitHub 파일 업데이트 시 SHA 불필요
3. **데이터 구조 이해**: Notion API 응답 형식 숙지 필수
4. **체계적 디버깅**: 노드별 개별 테스트가 핵심

---

## 🤝 기여 및 피드백

이 프로젝트는 지속적으로 발전하고 있습니다. 개선 아이디어나 버그 리포트는 언제든 환영합니다.

**프로젝트 상태**: 🟢 활발히 개발 중

**마지막 업데이트**: 2025-11-26
