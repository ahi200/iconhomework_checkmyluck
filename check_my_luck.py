from iconservice import *

TAG = 'TodayLuck'

class TodayLuck(IconScoreBase):
    _STAGE_INFO_NON_EXIST = 0
    _LUCK_RANK = "LUCK_RANK"
    _STAGE_INFO = "STAGE_INFO"
    _DEPLOY_STARTTIME = "DEPLOY_STARTTIME"
    _LIMIT_APPLY_USER = "LIMIT_APPLY_USER"
    _LIMIT_APPLY_DATE = "LIMIT_APPLY_DATE"
    _STAGE_LEVEL_1 = 1
    _STAGE_LEVEL_MAX = 100
    _ONE_DAY_SEC = 86400
    _APPLY_MAX_DATE = 20000
    _APPLY_MAX_USER = 200

    def __init__(self, db: IconScoreDatabase) -> None:
        super().__init__(db)
        self._luck_rank_array = ArrayDB(self._LUCK_RANK, db, value_type=str)
        self._stage_info = DictDB(self._STAGE_INFO, db, value_type=int, depth=2)
        self._deploy_starttime = VarDB(self._DEPLOY_STARTTIME, db ,value_type=int)
        self._limit_apply_user = DictDB(self._LIMIT_APPLY_USER, db, value_type=int, depth=2)
        self._limit_apply_date = DictDB(self._LIMIT_APPLY_DATE, db, value_type=int, depth=1)

    def on_install(self) -> None:
        super().on_install()
        self._deploy_starttime.set(int(self.block.timestamp/1000000))

    def on_update(self) -> None:
        super().on_update()

    def get_date_from_deploy(self)-> int:
        # current_timestamp = (int(self.block.timestamp/1000000))
        # deploy_starttime = self._deploy_starttime.get()
        # print("current_timestamp : ",current_timestamp)
        # print("deploy_starttime : ",deploy_starttime)
        return int(((self.block.timestamp/1000000) - self._deploy_starttime.get()) / self._ONE_DAY_SEC)

    @external(readonly=True)
    def hello(self) -> str:
        return "Hello"
    
    @external(readonly=True)
    def help(self) -> str:
        Logger.debug(f'Hello, enjoy your luck!', TAG)
        return "Hello, enjoy your luck"

    @external(readonly=True)
    def get_stage_info(self, addr: str) -> str:
        date = self.get_date_from_deploy()
        # print("date : ",date)
        if self._stage_info[date][addr] != self._STAGE_INFO_NON_EXIST:
            Logger.debug(f'My stage is {self._stage_info[date][addr]}', TAG)
            return "Stage : " + str(self._stage_info[date][addr])
        else:
            return "Stage info doesn't exist"

    @external
    def apply_stage(self) -> str:
        # For new user
        date = self.get_date_from_deploy()
        # print("date : ",date)
        if self._limit_apply_date[date] >= self._APPLY_MAX_DATE:
            # print("Today apply limit over")
            revert('Today apply limit over')
        
        if self._limit_apply_user[date][str(self.msg.sender)] >= self._APPLY_MAX_USER:
            # print("User apply limit over : ",str(self.msg.sender))
            revert('User apply limit over')

        self._limit_apply_date[date] += 1 
        self._limit_apply_user[date][str(self.msg.sender)] += 1

        if self._stage_info[date][str(self.msg.sender)] == self._STAGE_INFO_NON_EXIST:
            self._stage_info[date][str(self.msg.sender)] = self._STAGE_LEVEL_1
            self._luck_rank_array.put(str(self.msg.sender))

        if self._stage_info[date][str(self.msg.sender)] >= self._STAGE_LEVEL_1:
            stage_level = self._stage_info[date][str(self.msg.sender)]
        elif self._stage_info[date][str(self.msg.sender)] >= self._STAGE_LEVEL_MAX:
            # print("Stage Max")
            return "Stage Max"

        win = int.from_bytes(sha3_256(self.msg.sender.to_bytes() + str(self.block.timestamp).encode()), "big") % stage_level
        if win == 0:
            self._stage_info[date][str(self.msg.sender)] += 1
            Logger.debug(f'Success, Go to next stage!', TAG)
            # print("Success. stage : ",self._stage_info[date][str(self.msg.sender)])
            return "Success"
        else:
            Logger.debug(f'Fail.. try again!', TAG)
            # print("Fail")
            return "Fail"
    
    @external(readonly=True)
    def get_results(self, date: int) -> dict:
        valueArray = []
        for value in self._luck_rank_array:
            valueArray.append(value)
            # print("wallet address : ",value)
            valueArray.append(self._stage_info[date][value])
        return {'result': valueArray}
   
    @external(readonly=True)
    def get_user_apply_limit(self, addr: str) -> int:
        date = self.get_date_from_deploy()
        return int(self._limit_apply_user[date][addr])

    @external(readonly=True)
    def get_date_apply_limit(self) -> int:
        date = self.get_date_from_deploy()
        return self._limit_apply_date[date]

    @external(readonly=True)
    def get_block_timestamp(self) -> str:
        return self.block.timestamp
