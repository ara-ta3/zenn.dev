---
title: "PythonのProtocolを使ってDIを行う"
emoji: "🐍"
type: "tech" # tech: 技術記事 / idea: アイデア
topics: ["python", "protocol", "di", "dependency-injection"]
published: false
---

# 概要

PythonのProtocolを活用した依存性注入（DI）パターンを試してみました。  
ServiceクラスとRepositoryクラスの依存関係をProtocolで抽象化し、テスタビリティと保守性を向上させる方法についてサンプルコードと共に備忘録として残します。

## Protocolとは

PythonのProtocolは、構造的部分型（structural subtyping）を提供する仕組みです。  
型システムレベルでインターフェースを定義でき、実装クラスが明示的に継承しなくても、必要なメソッドを持っていれば型として認識されます。

## RepositoryProtocolの定義

```python
from typing import Protocol, List, Optional
from dataclasses import dataclass

@dataclass
class User:
    id: int
    name: str
    email: str

class UserRepositoryProtocol(Protocol):
    def find_by_id(self, user_id: int) -> Optional[User]:
        ...
    
    def find_all(self) -> List[User]:
        ...
    
    def save(self, user: User) -> User:
        ...
    
    def delete(self, user_id: int) -> bool:
        ...
```

## Repository実装クラス

```python
class InMemoryUserRepository:
    def __init__(self):
        self._users: dict[int, User] = {}
        self._next_id = 1
    
    def find_by_id(self, user_id: int) -> Optional[User]:
        return self._users.get(user_id)
    
    def find_all(self) -> List[User]:
        return list(self._users.values())
    
    def save(self, user: User) -> User:
        if user.id == 0:
            user.id = self._next_id
            self._next_id += 1
        self._users[user.id] = user
        return user
    
    def delete(self, user_id: int) -> bool:
        if user_id in self._users:
            del self._users[user_id]
            return True
        return False

class DatabaseUserRepository:
    # 実際のDB接続実装
    def find_by_id(self, user_id: int) -> Optional[User]:
        # DB検索ロジック
        pass
    
    def find_all(self) -> List[User]:
        # DB検索ロジック
        pass
    
    def save(self, user: User) -> User:
        # DB保存ロジック
        pass
    
    def delete(self, user_id: int) -> bool:
        # DB削除ロジック
        pass
```

## ServiceクラスでのProtocol活用

```python
class UserService:
    def __init__(self, user_repository: UserRepositoryProtocol):
        self._user_repository = user_repository
    
    def get_user(self, user_id: int) -> Optional[User]:
        return self._user_repository.find_by_id(user_id)
    
    def create_user(self, name: str, email: str) -> User:
        user = User(id=0, name=name, email=email)
        return self._user_repository.save(user)
    
    def get_all_users(self) -> List[User]:
        return self._user_repository.find_all()
    
    def update_user(self, user_id: int, name: str = None, email: str = None) -> Optional[User]:
        user = self._user_repository.find_by_id(user_id)
        if not user:
            return None
        
        if name is not None:
            user.name = name
        if email is not None:
            user.email = email
        
        return self._user_repository.save(user)
    
    def delete_user(self, user_id: int) -> bool:
        return self._user_repository.delete(user_id)
```

## DIコンテナの実装

```python
from typing import TypeVar, Type, Dict, Any, Callable

T = TypeVar('T')

class DIContainer:
    def __init__(self):
        self._services: Dict[Type[Any], Any] = {}
        self._factories: Dict[Type[Any], Callable[[], Any]] = {}
    
    def register_instance(self, service_type: Type[T], instance: T) -> None:
        self._services[service_type] = instance
    
    def register_factory(self, service_type: Type[T], factory: Callable[[], T]) -> None:
        self._factories[service_type] = factory
    
    def get(self, service_type: Type[T]) -> T:
        if service_type in self._services:
            return self._services[service_type]
        
        if service_type in self._factories:
            instance = self._factories[service_type]()
            self._services[service_type] = instance
            return instance
        
        raise ValueError(f"Service {service_type} is not registered")

# DIコンテナのセットアップ
def setup_container() -> DIContainer:
    container = DIContainer()
    
    # Repositoryの登録
    container.register_instance(
        UserRepositoryProtocol, 
        InMemoryUserRepository()
    )
    
    # Serviceの登録
    container.register_factory(
        UserService,
        lambda: UserService(container.get(UserRepositoryProtocol))
    )
    
    return container
```

## mainでのDI実装

```python
def main():
    # DIコンテナの初期化
    container = setup_container()
    
    # サービスの取得
    user_service = container.get(UserService)
    
    # ビジネスロジックの実行
    user = user_service.create_user("田中太郎", "tanaka@example.com")
    print(f"作成されたユーザー: {user}")
    
    all_users = user_service.get_all_users()
    print(f"全ユーザー: {all_users}")
    
    updated_user = user_service.update_user(user.id, name="田中次郎")
    print(f"更新されたユーザー: {updated_user}")

if __name__ == "__main__":
    main()
```

## テストでの活用

```python
import pytest
from unittest.mock import Mock

class TestUserService:
    def test_get_user_success(self):
        # Arrange
        mock_repository = Mock(spec=UserRepositoryProtocol)
        expected_user = User(id=1, name="テストユーザー", email="test@example.com")
        mock_repository.find_by_id.return_value = expected_user
        
        user_service = UserService(mock_repository)
        
        # Act
        result = user_service.get_user(1)
        
        # Assert
        assert result == expected_user
        mock_repository.find_by_id.assert_called_once_with(1)
    
    def test_create_user(self):
        # Arrange
        mock_repository = Mock(spec=UserRepositoryProtocol)
        created_user = User(id=1, name="新規ユーザー", email="new@example.com")
        mock_repository.save.return_value = created_user
        
        user_service = UserService(mock_repository)
        
        # Act
        result = user_service.create_user("新規ユーザー", "new@example.com")
        
        # Assert
        assert result == created_user
        mock_repository.save.assert_called_once()
```

# まとめ

PythonのProtocolとDIパターンを試してみました。  

- 型安全性とテスタビリティの向上
- 実装の切り替えが容易になる柔軟性
- インターフェースが明確になることによる保守性の向上

Protocolを使うことで、Pythonでも他言語同様に堅牢で保守性の高いアプリケーションを構築できそうです。
