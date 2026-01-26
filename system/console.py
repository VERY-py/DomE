import threading
import pygame

class Chat:
    def __init__(self, player, screen, name):
        self.user = name
        self.player = player
        self.screen = screen
        self.font = pygame.font.Font(None, 30)
        self.chat = {}
        receive_thread = threading.Thread(target=self.cmd, args=())
        receive_thread.daemon = True
        receive_thread.start()

    def cmd(self):
        while True:
            try:
                cmd = input().strip()
                cmd = cmd.split()
                if cmd[0].lower() == '/':
                    if cmd[1].lower() == 'tp' and len(cmd) == 4:
                        self.player.rect.x = cmd[2]
                        self.player.rect.y = cmd[3]
                        self.print_in_chat(f"Телепортировано на {cmd[2]} {cmd[3]}")
                        break
                    else:
                        self.print_in_chat(f"Неизвестная команда: {cmd}")
                else:
                    self.print_in_chat(cmd)
            except (EOFError, KeyboardInterrupt):
                break

    def print_in_chat(self, txt):
        text = self.font.render(txt, True, (255, 255, 255))
        self.screen.blit(text, (5, self.screen.get_height()))
        if self.user in self.chat.keys():
            for nick in self.chat.keys():
                if self.user == nick:
                    self.chat[nick] = txt
                    break
        else:
            self.chat[self.user] = txt