# Vue Event Handling - 개념 정리와 실습

## 0. 이 수업의 한 문장 요약

**사용자가 화면에서 행동하면, Vue가 그 행동을 감지해서 우리가 연결한 코드를 실행한다.**

예를 들어 버튼을 누르면 숫자가 증가하고, Enter를 누르면 댓글이 등록되고, 팝업 바깥을 누르면 팝업이 닫히는 것이 모두 이벤트 핸들링이다.

---

## 1. `v-on`과 `@` - 이벤트를 연결하는 문법

`v-on`은 HTML 요소의 이벤트를 감지한다. `@`는 `v-on:`의 짧은 표기다.

```vue
<!-- 같은 의미 -->
<button v-on:click="doSomething">클릭</button>
<button @click="doSomething">클릭</button>
```

가장 자주 쓰는 이벤트는 다음과 같다.

| 이벤트 | 언제 발생할까? |
| --- | --- |
| `@click` | 클릭했을 때 |
| `@input` | 입력값이 바뀔 때 |
| `@change` | 입력 후 포커스를 벗어날 때 |
| `@submit` | 폼을 제출할 때 |
| `@keyup` | 키에서 손을 뗐을 때 |
| `@keydown` | 키를 눌렀을 때 |

---

## 2. 인라인 핸들러와 메서드 핸들러

### 인라인 핸들러: 아주 짧은 동작

```vue
<button @click="count++">+1</button>
```

한 줄짜리 증감이나 토글처럼 의미가 분명한 동작에 적합하다.

### 메서드 핸들러: 이름 있는 동작

```vue
<script setup>
const showMessage = () => {
  alert('저장되었습니다!')
}
</script>

<template>
  <button @click="showMessage">저장</button>
</template>
```

함수에 괄호가 없는 이유는 지금 실행하라는 뜻이 아니라, **클릭할 때 실행할 함수를 등록한다**는 뜻이기 때문이다.

```vue
@click="showMessage"   <!-- 클릭할 때 실행 -->
@click="showMessage()" <!-- 클릭 순간 함수 호출 결과를 사용 -->
```

보통 이벤트 핸들러는 첫 번째 방식을 쓴다.

---

## 3. 이벤트 객체 `event` - 방금 무슨 일이 일어났는지

브라우저는 클릭이나 키보드 입력이 발생할 때마다 이벤트 정보를 담은 객체를 만든다.

```vue
<button @click="showPosition">좌표 확인</button>
```

```js
const showPosition = (event) => {
  console.log(event.clientX, event.clientY)
}
```

함수 이름만 넘기면 Vue가 이벤트 객체를 자동으로 첫 번째 인자로 전달한다.

자주 보는 정보:

| 값 | 의미 |
| --- | --- |
| `event.target` | 실제로 클릭된 요소 |
| `event.currentTarget` | 이벤트를 연결한 요소 |
| `event.target.value` | input 등에 입력된 값 |
| `event.clientX`, `event.clientY` | 화면 기준 클릭 좌표 |
| `event.key` | 누른 키, 예: `Enter`, `Escape` |

### 내 값과 이벤트를 같이 넘길 때: `$event`

```vue
<button @click="selectMember('회원 A', $event)">회원 A</button>
```

```js
const selectMember = (name, event) => {
  console.log(name)
  console.log(event.target.tagName)
}
```

`'회원 A'`를 직접 전달하기 시작했으므로, 이벤트 객체는 `$event`로 명시해야 한다.

---

## 4. 이벤트 버블링 - 클릭이 부모에게 전달되는 이유

HTML은 부모와 자식으로 중첩되어 있다. 자식 버튼을 클릭하면 그 클릭은 부모 영역에도 전달된다. 이를 **버블링**이라고 한다.

```vue
<div @click="handleParent">
  <button @click="handleChild">자식 버튼</button>
</div>
```

자식 버튼을 한 번 눌러도 `handleChild`와 `handleParent`가 모두 실행된다.

---

## 5. 이벤트 수식어 - 자주 쓰는 제어 장치

Vue는 자바스크립트 이벤트 메서드를 템플릿에서 짧게 쓸 수 있게 해 준다.

| 수식어 | 자바스크립트 의미 | 사용 상황 |
| --- | --- | --- |
| `.prevent` | `preventDefault()` | 링크 이동, 폼 새로고침 방지 |
| `.stop` | `stopPropagation()` | 자식 클릭이 부모로 전달되는 것 방지 |
| `.once` | 한 번 실행 후 해제 | 중복 제출 방지 |
| `.self` | 자기 자신을 직접 눌렀을 때만 실행 | 모달 바깥 영역 클릭 시 닫기 |
| `.enter` | Enter 키일 때 실행 | Enter로 입력 제출 |
| `.esc` | Esc 키일 때 실행 | Esc로 모달 닫기 |

### `.prevent`

```vue
<form @submit.prevent="save">
  <button>저장</button>
</form>
```

폼을 제출해도 페이지가 새로고침되지 않고 `save` 함수가 실행된다.

### `.stop`

```vue
<div @click="closeModal">
  <section @click.stop>
    팝업 내용: 여기 클릭은 팝업을 닫지 않는다.
  </section>
</div>
```

### 키 수식어

```vue
<input @keyup.enter="submitComment" />
```

Enter를 뗐을 때만 `submitComment`가 실행된다.

---

## 6. 지금 실습하는 순서

`src/App.vue`를 열고 개발 서버를 실행한 뒤, 아래를 직접 확인한다.

1. **카운트 +1**: `count`가 `ref`이므로 화면도 함께 바뀐다.
2. **함수 실행**: `@click="showMessage"`가 함수와 연결된다.
3. **클릭 좌표 확인**: 자동 전달된 `event.clientX`, `event.clientY`를 읽는다.
4. **회원 A 선택**: 문자열과 `$event`를 동시에 전달한다.
5. **이동하지 않는 링크**: `.prevent`가 기본 링크 이동을 막는다.
6. **일반 자식 버튼**: 자식과 부모 로그가 모두 남는다.
7. **`.stop` 자식 버튼**: 자식 로그만 남는다.

## 7. 마지막 확인 문제

아래를 말로 설명할 수 있으면 이번 챌린지는 완료다.

1. `@click="count++"`와 `@click="showMessage"`는 언제 각각 쓸까?
2. `$event`가 필요한 이유는 무엇일까?
3. 일반 자식 버튼과 `.stop` 자식 버튼의 로그 차이는 왜 생길까?
4. 폼 제출 시 `.prevent`를 쓰는 이유는 무엇일까?
