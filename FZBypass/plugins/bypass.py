from time import time
from re import match
from sys import executable
from os import execl
from pyrogram import enums
from asyncio import create_task, gather, sleep as asleep, create_subprocess_exec
from pyrogram.filters import command, private, user
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup, InlineQueryResultArticle, InputTextMessageContent
from pyrogram.enums import MessageEntityType
from pyrogram.errors import QueryIdInvalid
 
from FZBypass import Config, Bypass, BOT_START, LOGGER
from FZBypass.core.bypass_checker import direct_link_checker, is_excep_link
from FZBypass.core.bot_utils import chat_and_topics, convert_time
from FZBypass.core.exceptions import DDLException
 
 

START_TEXT = """Hey {mention},
 
**★ This is Bypasss Bot**
 
__✳️ Which can Bypass Various Shortener Links, Scrape links, and more.__
 
 
⌛ **BOT UP-TIME**:  `{bot_start_time}`
 """



@Bypass.on_message(command('start'))
async def start_msg(c, m):
 ###### For mention user
    last_name = f' {m.from_user.last_name}' if m.from_user.last_name else ''
    mention = f"[{m.from_user.first_name}{last_name}](tg://user?id={m.from_user.id})"

    bot_start_time = convert_time(time() - BOT_START)
 
    if not getattr(m, 'data', None):
        rango = await m.reply("<b>Processing..</b> ⏳", quote=True)
    else:
        rango = m.message
        
    await rango.edit(
         text=START_TEXT.format(mention=mention, bot_start_time=bot_start_time),
         reply_markup=InlineKeyboardMarkup(
             [
                 [
                     InlineKeyboardButton('MASTER 👑', url='https://t.me/RangoZex'),
                 ],
                 [
                     InlineKeyboardButton('Close ❌', callback_data='close')
                 ]
             ]
         ),
         disable_web_page_preview=True,
         parse_mode=enums.ParseMode.MARKDOWN
    )
 
 

########## Added Close button ✅ #######
@Bypass.on_callback_query(filters.regex('close$'))
async def close(c, m):
    await m.message.delete()
    await m.message.reply_to_message.delete() 


# @Bypass.on_message(command(['bypass', 'bp']) & chat_and_topics)
# async def bypass_check(client, message):
#     uid = message.from_user.id
#     if (reply_to := message.reply_to_message) and (reply_to.text is not None or reply_to.caption is not None):
#         txt = reply_to.text or reply_to.caption
#         entities = reply_to.entities or reply_to.caption_entities
#     elif len(message.command) > 1:
#         txt = message.text
#         entities = message.entities
#     else:
#         return await message.reply('<i>No Link Provided! 🙂</i>', quote=True)
    
#     wait_msg = await message.reply("<i>Bypassing...</i>", quote=True)
#     start = time()
 
#     link, tlinks, no = '', [], 0
#     atasks = []
#     for enty in entities:
#         if enty.type == MessageEntityType.URL:
#             link = txt[enty.offset:(enty.offset+enty.length)]
#         elif enty.type == MessageEntityType.TEXT_LINK:
#             link = enty.url
            
#         if link:
#             no += 1
#             tlinks.append(link)
#             atasks.append(create_task(direct_link_checker(link)))
#             link = ''
 
#     completed_tasks = await gather(*atasks, return_exceptions=True)
    
#     parse_data = []
URL_REGEX = r"https?://\S+"

@Bypass.on_message(filters.regex(URL_REGEX))
async def bypass_links(client, message):
    uid = message.from_user.id

    txt = message.text
    entities = message.entities

    wait_msg = await message.reply("<i>Bypassing...</i>", quote=True)
    start = time()

    tlinks, no = [], 0
    atasks = []

    for enty in entities:
        if enty.type == MessageEntityType.URL:
            link = txt[enty.offset:(enty.offset + enty.length)]
            no += 1
            tlinks.append(link)
            atasks.append(create_task(direct_link_checker(link)))

    completed_tasks = await gather(*atasks, return_exceptions=True)

    parse_data = [] 
    for result, link in zip(completed_tasks, tlinks):
        if isinstance(result, Exception):
            bp_link = f"<b>Bypass Error:</b> {result}"
        elif is_excep_link(link):
            bp_link = result
        else:
            bp_link = f"<b>📩 <a href='{result}'>BYPASS LINK</a></b>: <code>{result}</code>"
        
        if is_excep_link(link):
            parse_data.append(bp_link + "\n\n﹏﹏﹏﹏﹏﹏﹏﹏﹏﹏﹏﹏﹏﹏﹏\n\n")
        else:
            parse_data.append(f'<b>🔗 <a href="{link}">SOURCE LINK</a>:</b> <code>{link}</code>\n\n<b>📩 <a href="{bp_link}">BYPASS LINK</a>:</b> <code>{bp_link}</code>\n\n﹏﹏﹏﹏﹏﹏﹏﹏﹏﹏﹏﹏﹏﹏﹏\n')
            
    end = time()
 
    if len(parse_data) != 0:
        parse_data[-1] = parse_data[-1] + f"🔗 <i><b>Total Links : {no}</b>\n🧭 <b>Took Only <code>{convert_time(end - start)}</code></b></i> !\n#cc : {message.from_user.mention} ( #ID{message.from_user.id} )"
    tg_txt = ""
    for tg_data in parse_data:
        tg_txt += tg_data
        if len(tg_txt) > 4000:
            await wait_msg.edit(tg_txt, disable_web_page_preview=True)
            wait_msg = await message.reply("<i>Fetching...</i>", reply_to_message_id=wait_msg.id)
            tg_txt = ""
            await asleep(2.5)
    
    if tg_txt != "":
        await wait_msg.edit(tg_txt, disable_web_page_preview=True)
 
 
@Bypass.on_message(command('log') & user(Config.OWNER_ID))
async def send_logs(client, message):
    await message.reply_document('log.txt', quote=True)
 
 
@Bypass.on_message(command('restart') & user(Config.OWNER_ID))
async def restart(client, message):
    restart_message = await message.reply('<i>Restarting...</i>')
    await (await create_subprocess_exec('python3', 'update.py')).wait()
    with open(".restartmsg", "w") as f:
        f.write(f"{restart_message.chat.id}\n{restart_message.id}\n")
    execl(executable, executable, "-m", "FZBypass")
 
 
@Bypass.on_inline_query()
async def inline_query(client, query):
    answers = [] 
    string = query.query.lower()
    if string.startswith("!bp "):
        link = string.strip('!bp ')
        start = time()
        try:
            bp_link = await direct_link_checker(link)
            end = time()
            
            if not is_excep_link(link):
                bp_link = f"<b>🔗<a href='{link}'>SOURCE LINK:</a></b> <code>{link}</code>\n\n<b>📩 <a href='{bp_link}'>BYPASS LINK:</a></b> <code>{bp_link}</code>"
            answers.append(InlineQueryResultArticle(
                title="✅️ Bypass Link Success !",
                input_message_content=InputTextMessageContent(
                    f'{bp_link}\n\n﹏﹏﹏﹏﹏﹏﹏﹏﹏﹏﹏﹏﹏﹏﹏\n\n🧭 <b>Took Only <code>{convert_time(end - start)}</code></b>',
                    disable_web_page_preview=True,
                ),
                description=f"Bypass via !bp {link}",
                reply_markup=InlineKeyboardMarkup([
                        [InlineKeyboardButton('Bypass Again', switch_inline_query_current_chat="!bp ")]
                ])
            ))
        except Exception as e:
            bp_link = f"<b>Bypass Error:</b> {e}"
            end = time()
 
            answers.append(InlineQueryResultArticle(
                title="❌️ Bypass Link Error !",
                input_message_content=InputTextMessageContent(
                    f'<b>🔗 <a href="{link}">SOURCE LINK:</a></b> <code>{link}</code>\n📩 <a href="{bp_link}">BYPASS LINK</a>\n\n﹏﹏﹏﹏﹏﹏﹏﹏﹏﹏﹏﹏﹏﹏﹏\n\n🧭 <b>Took Only <code>{convert_time(end - start)}</code></b>',
                    disable_web_page_preview=True,
                ),
                description=f"Bypass via !bp {link}",
                reply_markup=InlineKeyboardMarkup([
                        [InlineKeyboardButton('Bypass Again', switch_inline_query_current_chat="!bp ")]
                ])
            ))    
        
    else:
        answers.append(InlineQueryResultArticle(
                title="♻️ Bypass Usage: In Line",
                input_message_content=InputTextMessageContent(
                    '''<b><i>Bypass Bot!</i></b>
    
    <i>A Powerful Elegant Multi Threaded Bot written in Python... which can Bypass Various Shortener Links, Scrape links, and More ... </i>
    
🎛 <b>Inline Use :</b> !bp [Single Link]''',
                ),
                description="Bypass via !bp [link]",
                reply_markup=InlineKeyboardMarkup([
                        [InlineKeyboardButton("Channel", url="https://t.me/MirrorPro"),
                        InlineKeyboardButton('Try Bypass', switch_inline_query_current_chat="!bp ")]
                ])
            ))
    try:
        await query.answer(
            results=answers,
            cache_time=0
        )
    except QueryIdInvalid:
        pass
