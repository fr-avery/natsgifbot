from discord.ext import commands
import covid

class Temp():
    def __init__(self,bot):
        self.bot = bot

    @commands.command()
    async def covid(self,*arg:str):
        """display information about COVID-19"""
        # if len(arg) == 0:
        #     await self.bot.say(covid.get_us())
        # else:
        #     if not arg[0].startswith('+') and not arg[0].startswith('-'):
        #         await self.bot.say(covid.get_state(arg[0]))
        await self.bot.say(covid.get_usa())

def setup(bot):
    bot.add_cog(Temp(bot))
