---
name: ant-design
description: Ant Design 컴포넌트 라이브러리 사용 규칙. import 패턴, ConfigProvider, theme 커스터마이징, Form/Table 패턴.
---

# Ant Design 컨벤션

---

## Import 패턴

```typescript
// ✅ 좋은 예: named import
import { Button, Form, Input, Table, Space } from 'antd';
import type { FormProps, TableProps, ColumnsType } from 'antd';

// ✅ 아이콘 import (별도 패키지)
import { SearchOutlined, CloseOutlined, PlusOutlined } from '@ant-design/icons';
```

---

## ConfigProvider & theme 커스터마이징

```typescript
// src/main.tsx 또는 App.tsx
import { ConfigProvider, theme } from 'antd';
import ko_KR from 'antd/locale/ko_KR';

const { defaultAlgorithm, darkAlgorithm } = theme;

function App() {
  return (
    <ConfigProvider
      locale={ko_KR}
      theme={{
        algorithm: defaultAlgorithm, // 또는 darkAlgorithm
        token: {
          colorPrimary: '#1677ff',
          borderRadius: 8,
          fontFamily: '"Pretendard", -apple-system, sans-serif',
          colorBgContainer: '#ffffff',
        },
        components: {
          Button: {
            borderRadius: 6,
          },
          Table: {
            borderRadius: 8,
          },
        },
      }}
    >
      <AppRoutes />
    </ConfigProvider>
  );
}
```

---

## Form 패턴

```typescript
import { Form, Input, Select, Button } from 'antd';
import type { FormProps } from 'antd';

interface OrderFormValues {
  name: string;
  status: 'pending' | 'active';
  description?: string;
}

function OrderForm() {
  const [form] = Form.useForm<OrderFormValues>();

  const onFinish: FormProps<OrderFormValues>['onFinish'] = (values) => {
    console.log('제출 값:', values);
  };

  const onFinishFailed: FormProps<OrderFormValues>['onFinishFailed'] = (errorInfo) => {
    console.log('실패:', errorInfo);
  };

  return (
    <Form
      form={form}
      layout="vertical"
      onFinish={onFinish}
      onFinishFailed={onFinishFailed}
      initialValues={{ status: 'pending' }}
    >
      <Form.Item
        label="주문명"
        name="name"
        rules={[{ required: true, message: '주문명을 입력해주세요.' }]}
      >
        <Input placeholder="주문명 입력" />
      </Form.Item>

      <Form.Item
        label="상태"
        name="status"
        rules={[{ required: true }]}
      >
        <Select options={[
          { value: 'pending', label: '대기중' },
          { value: 'active', label: '진행중' },
        ]} />
      </Form.Item>

      <Form.Item>
        <Button type="primary" htmlType="submit">
          저장
        </Button>
      </Form.Item>
    </Form>
  );
}
```

---

## Table 패턴

```typescript
import { Table, Space, Button, Tag } from 'antd';
import type { TableProps, ColumnsType } from 'antd';

interface Order {
  id: string;
  name: string;
  status: 'pending' | 'active' | 'done';
  createdAt: string;
}

const columns: ColumnsType<Order> = [
  {
    title: '주문 ID',
    dataIndex: 'id',
    key: 'id',
    width: 100,
  },
  {
    title: '주문명',
    dataIndex: 'name',
    key: 'name',
    sorter: (a, b) => a.name.localeCompare(b.name),
  },
  {
    title: '상태',
    dataIndex: 'status',
    key: 'status',
    render: (status: Order['status']) => {
      const colorMap = { pending: 'gold', active: 'blue', done: 'green' };
      const labelMap = { pending: '대기중', active: '진행중', done: '완료' };
      return <Tag color={colorMap[status]}>{labelMap[status]}</Tag>;
    },
    filters: [
      { text: '대기중', value: 'pending' },
      { text: '진행중', value: 'active' },
    ],
    onFilter: (value, record) => record.status === value,
  },
  {
    title: '액션',
    key: 'action',
    render: (_, record) => (
      <Space>
        <Button size="small" onClick={() => handleEdit(record)}>수정</Button>
        <Button size="small" danger onClick={() => handleDelete(record.id)}>삭제</Button>
      </Space>
    ),
  },
];

function OrderTable() {
  const { data, isLoading } = useOrderQuery();

  const tableProps: TableProps<Order> = {
    columns,
    dataSource: data?.orders,
    rowKey: 'id',
    loading: isLoading,
    pagination: {
      pageSize: 20,
      showSizeChanger: true,
      showTotal: (total) => `전체 ${total}건`,
    },
    scroll: { x: 800 },
  };

  return <Table {...tableProps} />;
}
```

---

## 주요 컴포넌트 패턴

### Modal

```typescript
import { Modal, Button } from 'antd';
import { useState } from 'react';

function OrderModal() {
  const [open, setOpen] = useState(false);

  return (
    <>
      <Button onClick={() => setOpen(true)}>주문 추가</Button>
      <Modal
        title="주문 추가"
        open={open}
        onOk={() => setOpen(false)}
        onCancel={() => setOpen(false)}
        footer={[
          <Button key="cancel" onClick={() => setOpen(false)}>취소</Button>,
          <Button key="submit" type="primary" onClick={handleSubmit}>저장</Button>,
        ]}
      >
        <OrderForm />
      </Modal>
    </>
  );
}
```

### Notification & Message

```typescript
import { App } from 'antd';

// ✅ App 컴포넌트 내부에서 훅 사용 (v5+)
function OrderActions() {
  const { message, notification } = App.useApp();

  const handleSave = async () => {
    try {
      await saveOrder();
      message.success('저장되었습니다.');
    } catch {
      notification.error({
        message: '저장 실패',
        description: '다시 시도해주세요.',
      });
    }
  };

  return <Button onClick={handleSave}>저장</Button>;
}

// src/main.tsx - App 컴포넌트로 래핑 필수
function Root() {
  return (
    <ConfigProvider>
      <App>
        <AppRoutes />
      </App>
    </ConfigProvider>
  );
}
```

---

## useToken 훅

```typescript
import { theme } from 'antd';

function StyledComponent() {
  const { token } = theme.useToken();

  return (
    <div
      style={{
        padding: token.paddingMD,
        borderRadius: token.borderRadius,
        backgroundColor: token.colorBgContainer,
        color: token.colorText,
      }}
    >
      내용
    </div>
  );
}
```

---

## 체크리스트

- [ ] `ConfigProvider`로 locale 및 theme 설정?
- [ ] `App` 컴포넌트로 래핑해 `message`/`notification` 훅 사용?
- [ ] Form에 `Form.useForm()` 사용?
- [ ] Table의 `rowKey` 지정?
- [ ] ColumnsType으로 타입 안전성 확보?
- [ ] 아이콘은 `@ant-design/icons`에서 import?
