import view
import config
import model


if __name__ == "__main__":
    model.bot.run(config.TOKEN, log_handler=None)