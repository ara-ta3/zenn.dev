---
title: "PythonのProtocolとdependency-injectorでDIする"
emoji: "🐍"
type: "tech"
topics: ["python", "protocol", "di", "dependency-injector"]
published: false
---

# 概要

Python の Protocol と `dependency-injector` を活用した依存性注入（DI）パターンを試してみました。  
Service クラスと Repository クラスの依存関係を Protocol で抽象化し、テスタビリティと保守性を向上させる方法についてサンプルコードと共に備忘録として残します。

## Protocolとは

Pythonの `Protocol` は、構造的部分型（structural subtyping）を導入するための機能です。これにより、クラスが特定のインタフェースを明示的に継承していなくても、必要なメソッドや属性を持ってさえいれば、そのインタフェースを満たすと見なされます。これによって、より柔軟な型付けが可能になります。

## RepositoryProtocolの定義

まずは、データアクセス層のインタフェースを `Protocol` を使って定義します。

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

## ServiceクラスでのProtocol活用

次に、`UserService` が具象クラスではなく `UserRepositoryProtocol` に依存するように実装します。これにより、`UserService` はデータアクセスの具体的な実装から切り離されます。

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

## Repositoryの実装

`UserRepositoryProtocol` を満たす具象クラスを実装します。ここでは、オンメモリでの実装と、データベースを利用する場合のスケルトン（骨格）を示します。

### オンメモリ実装

```python
class UserRepositoryOnMemory:
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
```

### データベース実装（スケルトン）

```python
class UserRepositoryOnDatabase:
    def find_by_id(self, user_id: int) -> Optional[User]:
        # データベースからの検索処理
        pass

    def find_all(self) -> List[User]:
        # データベースからの検索処理
        pass

    def save(self, user: User) -> User:
        # データベースへの保存処理
        pass

    def delete(self, user_id: int) -> bool:
        # データベースからの削除処理
        pass
```

## DIコンテナの実装 (dependency-injector)

依存性の注入には、専用ライブラリ `dependency-injector` を利用します。これにより、依存関係の管理がより宣言的かつシンプルになります。

`pip install dependency-injector` でインストールできます。

```python
from dependency_injector import containers, providers

class Container(containers.DeclarativeContainer):
    config = providers.Configuration()

    user_repository = providers.Singleton(
        UserRepositoryOnMemory
    )

    user_service = providers.Factory(
        UserService,
        user_repository=user_repository,
    )
```

## mainでのDI実装

アプリケーションの起動時にコンテナを初期化し、必要なサービスを取得します。

```python
def main():
    container = Container()
    user_service = container.user_service()

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

`Protocol` に依存しているため、DIライブラリの変更はテストコードに影響を与えません。引き続き `unittest.mock.Mock` を使って、Repositoryの振る舞いを模倣したテストが可能です。

```python
import pytest
from unittest.mock import Mock

class TestUserService:
    def test_get_user_success(self):
        mock_repository = Mock(spec=UserRepositoryProtocol)
        expected_user = User(id=1, name="テストユーザー", email="test@example.com")
        mock_repository.find_by_id.return_value = expected_user

        user_service = UserService(mock_repository)

        result = user_service.get_user(1)

        assert result == expected_user
        mock_repository.find_by_id.assert_called_once_with(1)

    def test_create_user(self):
        mock_repository = Mock(spec=UserRepositoryProtocol)
        created_user = User(id=1, name="新規ユーザー", email="new@example.com")
        mock_repository.save.return_value = created_user

        user_service = UserService(mock_repository)

        result = user_service.create_user("新規ユーザー", "new@example.com")

        assert result == created_user
        # 呼び出し時の引数を検証する
        mock_repository.save.assert_called_once()
        saved_user = mock_repository.save.call_args[0][0]
        assert saved_user.name == "新規ユーザー"
        assert saved_user.email == "new@example.com"

```

# まとめ

Python の Protocol と `dependency-injector` を使った DI パターンを試してみました。

- **型安全性とテスタビリティの向上**: Protocolにより、インタフェースが明確になり、安全なモックが可能になる。
- **実装の切り替えが容易になる柔軟性**: `dependency-injector` を使うことで、設定ファイルなどに応じて使用する実装を簡単に切り替えられる。
- **コードの簡潔化**: 自作のDIコンテナと比べて、`dependency-injector` はより宣言的でコードがシンプルになる。

Protocol と DI ライブラリを組み合わせることで、Python でも堅牢で保守性の高いアプリケーションを効率的に構築できそうです。
