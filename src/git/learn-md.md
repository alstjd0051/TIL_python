# Learn Markdown

<h1>Heading Text</h1>

h1 ~ h6 : # ~ ######

# A

### B (이렇게 하면 안됨)

## Vim mode

- <ul><li>Unordered list</li></ul>
- Normal mode: press esc on any mode
- Insert mode: press i on Normal mode
- Visual mode: press v on Normal mode
- Command-line mode: press : on Normal mode
  - :{n} - Move to nth line
  - :set nu - Set line number
  - :w - Save
  - :q - Quit
  - :wq - Save and Quit
  - :q! - Override(저장 안하고 나가기)

## Lunch Menu

1. <ol><li>Ordered list</li></ol>
2. Sujebi
3. Kalguksu
4. Gomtang

## Paragraph

그냥 쓰시면 한 문단이 됩니다.

두번째 문단은 엔터를 두번 치시면 됩니다.
얘는 세번째 문단 같지만, 사실은 두번째 문단의 두번째 문장입니다.

<p>This is paragraph.</p>

## Image & Link

<img src="">
![](./img/cats.jpg)
![](https://www.google.com/logo.png)

<a href="https://www.google.com/">Go to google</a>
[Go to google](https://www.google.com)

## Code block

문장속에서 특정한 부분을 강조하고 싶을 때, `backquote`를 쓰시면 됩니다.

For example, Enter `$ git clone {repo addr}` to clone your repository.

```python
def hello(name: str) -> str:
    return f'Hello, {name}'


if __name__ == '__main__':
    print(hello('John'))
```

```shell
$ git clone {repo addr}
$ cd {repo name}
$ pip install -r requirements.txt
$ python main.py
```

## Math

문장에서 표현할때에는 $y = ax + b$ 를 사용.

$$
y = ax + b
$$
