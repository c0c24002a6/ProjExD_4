import math
import os
import random
import sys
import time
import pygame as pg

WIDTH = 1100  # ゲームウィンドウの幅
HEIGHT = 650  # ゲームウィンドウの高さ
os.chdir(os.path.dirname(os.path.abspath(__file__)))


def check_bound(obj_rct: pg.Rect) -> tuple[bool, bool]:
    """
    オブジェクトが画面内or画面外を判定し，真理値タプルを返す関数
    引数：こうかとんや爆弾，ビームなどのRect
    戻り値：横方向，縦方向のはみ出し判定結果（画面内：True／画面外：False）
    """
    yoko, tate = True, True
    if obj_rct.left < 0 or WIDTH < obj_rct.right:
        yoko = False
    if obj_rct.top < 0 or HEIGHT < obj_rct.bottom:
        tate = False
    return yoko, tate


def calc_orientation(org: pg.Rect, dst: pg.Rect) -> tuple[float, float]:
    """
    orgから見て，dstがどこにあるかを計算し，方向ベクトルをタプルで返す
    引数1 org：爆弾SurfaceのRect
    引数2 dst：こうかとんSurfaceのRect
    戻り値：orgから見たdstの方向ベクトルを表すタプル
    """
    x_diff, y_diff = dst.centerx - org.centerx, dst.centery - org.centery
    norm = math.sqrt(x_diff ** 2 + y_diff ** 2)
    return x_diff / norm, y_diff / norm


class Bird(pg.sprite.Sprite):
    """
    ゲームキャラクター（こうかとん）に関するクラス
    """
    delta = {  # 押下キーと移動量の辞書
        pg.K_UP: (0, -1),
        pg.K_DOWN: (0, 1),
        pg.K_LEFT: (-1, 0),
        pg.K_RIGHT: (1, 0),
    }


    def __init__(self, num: int, xy: tuple[int, int]):
        """
        こうかとん画像Surfaceを生成する
        引数1 num：こうかとん画像ファイル名の番号
        引数2 xy：こうかとん画像の位置座標タプル
        """
        super().__init__()
        img0 = pg.transform.rotozoom(pg.image.load(f"fig/{num}.png"), 0, 0.9)
        img = pg.transform.flip(img0, True, False)  # デフォルトのこうかとん
        self.imgs = {
            (+1, 0): img,  # 右
            (+1, -1): pg.transform.rotozoom(img, 45, 0.9),  # 右上
            (0, -1): pg.transform.rotozoom(img, 90, 0.9),  # 上
            (-1, -1): pg.transform.rotozoom(img0, -45, 0.9),  # 左上
            (-1, 0): img0,  # 左
            (-1, +1): pg.transform.rotozoom(img0, 45, 0.9),  # 左下
            (0, +1): pg.transform.rotozoom(img, -90, 0.9),  # 下
            (+1, +1): pg.transform.rotozoom(img, -45, 0.9),  # 右下
        }
        self.dire = (+1, 0)
        self.image = self.imgs[self.dire]
        self.rect = self.image.get_rect()
        self.rect.center = xy
        self.speed = 10

    def change_img(self, num: int, screen: pg.Surface):
        """
        こうかとん画像を切り替え，画面に転送する
        引数1 num：こうかとん画像ファイル名の番号
        引数2 screen：画面Surface
        """
        self.image = pg.transform.rotozoom(pg.image.load(f"fig/{num}.png"), 0, 0.9)
        screen.blit(self.image, self.rect)

    def update(self, key_lst: list[bool], screen: pg.Surface):
        """
        押下キーに応じてこうかとんを移動させる
        左Shiftキーを押したときに移動速度を変える
        引数1 key_lst：押下キーの真理値リスト
        引数2 screen：画面Surface
        """
        if key_lst[pg.K_LSHIFT]:  
            self.speed = 20
        else:
            self.speed = 10
        sum_mv = [0, 0]
        for k, mv in __class__.delta.items():
            if key_lst[k]:
                sum_mv[0] += mv[0]
                sum_mv[1] += mv[1]
        self.rect.move_ip(self.speed*sum_mv[0], self.speed*sum_mv[1])
        if check_bound(self.rect) != (True, True):
            self.rect.move_ip(-self.speed*sum_mv[0], -self.speed*sum_mv[1])
        if not (sum_mv[0] == 0 and sum_mv[1] == 0):
            self.dire = tuple(sum_mv)
            self.image = self.imgs[self.dire]
        screen.blit(self.image, self.rect)


class Bomb(pg.sprite.Sprite):
    """
    爆弾に関するクラス
    """
    colors = [(255, 0, 0), (0, 255, 0), (0, 0, 255), (255, 255, 0), (255, 0, 255), (0, 255, 255)]

    def __init__(self, emy, bird: Bird):
        """
        爆弾円Surfaceを生成する
        引数1 emy：爆弾を投下する敵機
        引数2 bird：攻撃対象のこうかとん
        """
        super().__init__()
        rad = random.randint(10, 50)  # 爆弾円の半径：10以上50以下の乱数
        self.image = pg.Surface((2*rad, 2*rad))
        color = random.choice(__class__.colors)  # 爆弾円の色：クラス変数からランダム選択
        pg.draw.circle(self.image, color, (rad, rad), rad)
        self.image.set_colorkey((0, 0, 0))
        self.rect = self.image.get_rect()
        # 爆弾を投下するemyから見た攻撃対象のbirdの方向を計算
        self.vx, self.vy = calc_orientation(emy.rect, bird.rect)  
        self.rect.centerx = emy.rect.centerx
        self.rect.centery = emy.rect.centery+emy.rect.height//2
        self.speed = 6
        self.state = "active"

    def update(self):
        """
        爆弾を速度ベクトルself.vx, self.vyに基づき移動させる
        引数 screen：画面Surface
        """
        self.rect.move_ip(self.speed * self.vx, self.speed * self.vy)
        if check_bound(self.rect) != (True, True):
            self.kill()


class Beam(pg.sprite.Sprite):
    """
    ビームに関するクラス
    """
    def __init__(self, bird: Bird):
        """
        ビーム画像Surfaceを生成する
        引数 bird：ビームを放つこうかとん
        """
        super().__init__()
        self.vx, self.vy = bird.dire
        angle = math.degrees(math.atan2(-self.vy, self.vx))
        self.image = pg.transform.rotozoom(pg.image.load(f"fig/beam.png"), angle, 1.0)
        self.vx = math.cos(math.radians(angle))
        self.vy = -math.sin(math.radians(angle))
        self.rect = self.image.get_rect()
        self.rect.centery = bird.rect.centery+bird.rect.height*self.vy
        self.rect.centerx = bird.rect.centerx+bird.rect.width*self.vx
        self.speed = 10

    def update(self):
        """
        ビームを速度ベクトルself.vx, self.vyに基づき移動させる
        引数 screen：画面Surface
        """
        self.rect.move_ip(self.speed*self.vx, self.speed*self.vy)
        if check_bound(self.rect) != (True, True):
            self.kill()


class Explosion(pg.sprite.Sprite):
    """
    爆発に関するクラス
    """
    def __init__(self, obj: "Bomb|Enemy", life: int):
        """
        爆弾が爆発するエフェクトを生成する
        引数1 obj：爆発するBombまたは敵機インスタンス
        引数2 life：爆発時間
        """
        super().__init__()
        img = pg.image.load(f"fig/explosion.gif")
        self.imgs = [img, pg.transform.flip(img, 1, 1)]
        self.image = self.imgs[0]
        self.rect = self.image.get_rect(center=obj.rect.center)
        self.life = life

    def update(self):
        """
        爆発時間を1減算した爆発経過時間_lifeに応じて爆発画像を切り替えることで
        爆発エフェクトを表現する
        """
        self.life -= 1
        self.image = self.imgs[self.life//10%2]
        if self.life < 0:
            self.kill()

class Gravity(pg.sprite.Sprite):
    """ 
    重力に関するクラス
    """
    def __init__(self, life: int):  # 重力の持続時間
        super().__init__()  
        self.image = pg.Surface((WIDTH, HEIGHT))  # 画面全体を覆うSurface
        self.rect = self.image.get_rect()  # 画面全体を覆う
        self.rect.center = WIDTH//2, HEIGHT//2  # 画面の中心に配置
        pg.draw.rect(self.image, (0, 0, 0), (0, 0, WIDTH, HEIGHT))  # 黒色で塗りつぶす
        self.image.set_alpha(128)  # 半透明にする
        self.life = life  # 重力の持続時間
    
    def update(self):  
        self.life -= 1  # 重力の持続時間を1減らす
        if self.life < 0:  # 持続時間が0以下になったら
            self.kill()  

class Enemy(pg.sprite.Sprite):
    """
    敵機に関するクラス
    """
    imgs = [pg.image.load(f"fig/alien{i}.png") for i in range(1, 4)]

    def __init__(self):
        super().__init__()
        self.image = pg.transform.rotozoom(random.choice(Enemy.imgs), 0, 0.8)
        self.original_image = self.image.copy()
        self.rect = self.image.get_rect(center=(random.randint(0, WIDTH), 0))
        self.vx, self.vy = 0, 6
        self.bound = random.randint(50, HEIGHT // 2)  # 停止位置
        self.state = "down"  # 降下状態or停止位置
        self.interval = random.randint(50, 300)  # 爆弾投下インターバル

    def reset_image(self):
        self.image = self.original_image.copy()

    def update(self):
        """
        敵機を速度ベクトルself.vyに基づき移動（降下）させる
        ランダムに決めた停止位置_boundまで降下したら，_stateを停止状態に変更する
        引数 screen：画面Surface
        """
        if self.rect.centery > self.bound:
            self.vy = 0
            self.state = "stop"
        self.rect.move_ip(self.vx, self.vy)


class EMP:
    """
    発動時に存在する敵機と爆弾を無効化する
    敵機：爆弾投下できなくなる
    爆弾：動きが鈍くなる／ぶつかったら起爆せずに消滅する
    """
    def __init__(self, enemy_group, bomb_group, screen):
        self.enemy_group = enemy_group
        self.bomb_group = bomb_group
        self.screen = screen
        self.active = True  # 表示用フラグ
        self.timer = 3  # 無効化持続時間（秒）
        self.start_time = pg.time.get_ticks()

        # 敵機の無効化
        for enemy in self.enemy_group:
            enemy.interval = math.inf
            enemy.image = pg.transform.laplacian(enemy.image)

        # 爆弾の無効化
        for bomb in self.bomb_group:
            bomb.speed *= 0.5
            bomb.state = "inactive"  # 自作の状態管理フラグが必要

    def update(self):
        # 画面全体に透明度のある黄色の矩形を表示（0.05秒間）
        if self.active:
            overlay = pg.Surface(self.screen.get_size(), pg.SRCALPHA)
            overlay.fill((255, 255, 0, 100))  # RGBA、透明度100
            self.screen.blit(overlay, (0, 0))
            self.active = False  # 1フレームだけ表示

        # 無効化解除処理（3秒経過で元に戻す）
        elapsed_time = (pg.time.get_ticks() - self.start_time) / 1000
        if elapsed_time > self.timer:
            for enemy in self.enemy_group:
                enemy.interval = 1000  # 元の発射間隔に戻す（適宜調整）
                enemy.reset_image()  # 元の画像に戻す処理をEnemy側に実装

            for bomb in self.bomb_group:
                bomb.speed *= 2  # 半減させたので2倍で元に戻す
                bomb.state = "active"
            return True  # 終了フラグ
        return False


class Score:
    """
    打ち落とした爆弾，敵機の数をスコアとして表示するクラス
    爆弾：1点
    敵機：10点
    """
    def __init__(self):
        self.font = pg.font.Font(None, 50)
        self.color = (0, 0, 255)
        self.value = 0
        self.image = self.font.render(f"Score: {self.value}", 0, self.color)
        self.rect = self.image.get_rect(center=(100, HEIGHT - 50))

    def update(self, screen: pg.Surface):
        self.image = self.font.render(f"Score: {self.value}", 0, self.color)
        screen.blit(self.image, self.rect)

class Shield(pg.sprite.Sprite):
    """
    こうかとんの防御シールド
    """
    def __init__(self, bird: Bird, life: int):
        super().__init__()
        self.bird = bird
        self.life = life

        height = self.bird.rect.height * 2
        self.original_image = pg.Surface((20, height), pg.SRCALPHA)
        pg.draw.rect(self.original_image, (0, 0, 255), (0, 0, 20, height))

        self.image = self.original_image
        self.rect = self.image.get_rect(center=self.bird.rect.center)

    def update(self):
        self.life -= 1
        if self.life < 0:
            self.kill()

        vx, vy = self.bird.dire
        angle = math.degrees(math.atan2(-vy, vx))

        self.image = pg.transform.rotozoom(self.original_image, angle, 1)
        self.rect = self.image.get_rect(center=self.bird.rect.center)

        self.rect.centerx += vx * self.bird.rect.width
        self.rect.centery += vy * self.bird.rect.height

def main():
    pg.display.set_caption("真！こうかとん無双")
    screen = pg.display.set_mode((WIDTH, HEIGHT))
    bg_img = pg.image.load("fig/pg_bg.jpg")
    score = Score()
    bird = Bird(3, (900, 400))
    bombs = pg.sprite.Group()
    beams = pg.sprite.Group()
    exps = pg.sprite.Group()
    emys = pg.sprite.Group()
    gravity = pg.sprite.Group()
    shields = pg.sprite.Group()
    emp = None

    tmr = 0
    clock = pg.time.Clock()
    while True:
        key_lst = pg.key.get_pressed()
        for event in pg.event.get():
            if event.type == pg.QUIT:
                return 0
            if event.type == pg.KEYDOWN:
                if event.key == pg.K_SPACE:
                    beams.add(Beam(bird))
                if event.key == pg.K_e and score.value >= 20 and emp is None:
                    emp = EMP(emys, bombs, screen)
                    score.value -= 20

            if event.type == pg.KEYDOWN and event.key == pg.K_SPACE:
                beams.add(Beam(bird))
            if event.type == pg.KEYDOWN and event.key == pg.K_RETURN:  # Enterキーで重力を発動
                if score.value >= 200:  # スコアが200以上のときのみ発動
                    score.value -=200  # スコアを200減らす
                    gravity.add(Gravity(400))  # 400フレームの重力を発動 
            if event.type == pg.KEYDOWN and event.key == pg.K_s and score.value >= 50 and len(shields) == 0:
                shields.add(Shield(bird, 400))  
                score.value -= 50    
        screen.blit(bg_img, [0, 0])

        if tmr % 200 == 0:  # 200フレームに1回，敵機を出現させる
            emys.add(Enemy())

        for emy in emys:
            if emy.state == "stop" and tmr % emy.interval == 0:
                # 敵機が停止状態に入ったら，intervalに応じて爆弾投下
                bombs.add(Bomb(emy, bird))

        for emy in pg.sprite.groupcollide(emys, beams, True, True):
            exps.add(Explosion(emy, 100))  # 爆発エフェクト
            score.value += 10  # 10点アップ
            bird.change_img(6, screen)  # こうかとん喜びエフェクト

        for bomb in pg.sprite.groupcollide(bombs, beams, True, True):
            exps.add(Explosion(bomb, 50))  # 爆発エフェクト
            score.value += 1  # 1点アップ

        for bomb in pg.sprite.spritecollide(bird, bombs, False):
            if bomb.state == "inactive":
                bomb.kill()
                continue
        for emy in pg.sprite.groupcollide(emys, gravity, True, False).keys():  # 重力と衝突した敵機リスト
            exps.add(Explosion(emy, 100))  # 爆発エフェクト
            score.value += 10  # 10点アップ
            bird.change_img(6, screen)  # こうかとん喜びエフェクト
        for bomb in pg.sprite.groupcollide(bombs, gravity, True, False).keys():  # 重力と衝突した爆弾リスト
            exps.add(Explosion(bomb, 50))  # 爆発エフェクト               
            score.value += 1  # 1点アップ
            bird.change_img(6, screen)  # こうかとん喜びエフェクト

        for bomb in pg.sprite.spritecollide(bird, bombs, True):  # こうかとんと衝突した爆弾リスト
            bird.change_img(8, screen)  # こうかとん悲しみエフェクト
            score.update(screen)
            pg.display.update()
            time.sleep(2)
            return
        
        # 毎フレームのEMP処理
        if emp:
            if emp.update():
                emp = None  # EMP終了
        
       
        for bomb in pg.sprite.groupcollide(bombs,shields, True,True).keys():  # 防御壁と衝突した爆弾を削除
            exps.add(Explosion(bomb, 50))  # 爆発エフェクト


        bird.update(key_lst, screen)
        beams.update()
        beams.draw(screen)
        emys.update()
        emys.draw(screen)
        bombs.update()
        bombs.draw(screen)
        exps.update()
        exps.draw(screen)
        score.update(screen)
        gravity.update()
        gravity.draw(screen)
        shields.update()
        shields.draw(screen)
        pg.display.update()
        tmr += 1
        clock.tick(50)

if __name__ == "__main__":
    pg.init()
    main()
    pg.quit()
    sys.exit()
   