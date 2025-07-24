---
title: "PythonのProtocolとdependency-injectorでDIする"
emoji: "🐍"
type: "tech"
topics: ["python", "protocol", "di", "dependency-injector"]
published: false
---

# 概要

Pythonには他の静的型付け言語のような明確な `interface` キーワードがありませんが、それに代わる `Protocol` という概念を最近知りました。

そこで、個人的に好んで使っている「ServiceクラスにRepositoryを注入する」というDI（依存性注入）パターンを、この `Protocol` を使ってPythonでどう実現できるか試してみることにしました。

本記事では、`dependency-injector` も組み合わせ、その具体的な実装方法をサンプルコードと共に備忘録として残します。

# Protocolでインタフェースを定義する

まずは、アプリケーションの疎結合性を高めるためのインタフェースを `Protocol` を使って定義します。

## Protocolとは

Pythonの `Protocol` は、Go言語の `interface` に非常によく似た概念です。

Goでは、ある型が特定の `interface` で定義されたメソッドをすべて実装していれば、その型は明示的に `implements` と書かなくても、その `interface` を満たすと見なされます。

Pythonの `Protocol` もこれと同じ考え方に基づいています。クラスが `Protocol` で定義されたメソッドや属性を（同じシグネチャで）持っていれば、そのクラスは `Protocol` を明示的に継承していなくても、その `Protocol` 型として扱うことができます。このような仕組みは、いわゆる構造的部分型（structural subtyping）と呼ばれるようです。

これにより、具象クラスと、それを利用するコードとの間に疎結合な関係を築くことができ、柔軟でテストしやすい設計が可能になります。

## Repositoryのインタフェースを定義する

今回はデータアクセス層のインタフェースとして `UserRepositoryProtocol` を定義します。

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

# 主要なコンポーネントの実装

次に、定義した `Protocol` を利用して、アプリケーションの主要な部品の `Service` と `Repository` を実装します。

## Serviceクラス

`UserService` は、具体的な `Repository` の実装ではなく、先ほど定義した `UserRepositoryProtocol` に依存します。

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

## Repositoryクラス

`UserRepositoryProtocol` を満たす具象クラスとして、オンメモリで動作する `UserRepositoryOnMemory` を実装します。

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

# DIによるアプリケーションの組み立て

実装したコンポーネントを `dependency-injector` を使って結合し、アプリケーションとして実行できるようにします。

## DIコンテナの定義

`dependency-injector` を使って、どのインタフェース（`Protocol`）にどの具象クラスを注入するかを定義します。

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

## アプリケーションの実行

コンテナから `UserService` のインスタンスを取得して、ビジネスロジックを実行します。

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

# テスト容易性の確認

`Protocol` を使うことで、テストが非常に書きやすくなります。`Service` のテストをする際に、本物の `Repository` の代わりにモックオブジェクトを注入できるためです。

## Protocolを使ったユニットテスト

`unittest.mock.Mock` を使って `UserRepositoryProtocol` の振る舞いを模倣し、`UserService` をテストします。

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
