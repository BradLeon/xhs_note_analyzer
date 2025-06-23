from crewai import Agent, Crew, Process, Task, LLM
from crewai.project import CrewBase, agent, crew, task
from browser_use import Agent as BrowserAgent


# If you want to run a snippet of code before or after the crew starts,
# you can use the @before_kickoff and @after_kickoff decorators
# https://docs.crewai.com/concepts/crews#example-crew-class-with-decorators


@CrewBase
class PoemCrew:
    """Poem Crew"""

    # Learn more about YAML configuration files here:
    # Agents: https://docs.crewai.com/concepts/agents#yaml-configuration-recommended
    # Tasks: https://docs.crewai.com/concepts/tasks#yaml-configuration-recommended
    agents_config = "config/agents.yaml"
    tasks_config = "config/tasks.yaml"

    task = """
    1. 登录小红书聚光平台: https://ad.xiaohongshu.com/
    2. 跳转到菜单：数据->笔记->内容灵感页面：https://ad.xiaohongshu.com/microapp/traffic-guide/contentInspiration
    3. 下滑到页面底部，“核心笔记”部分。
    4. 浏览笔记列表中，每个笔记的标题和封面，只选择与推广标的:{promotion target}主题相关或接近的笔记。 例如推广标的是“国企央企求职”，则相关或接近的笔记主题可以是“考编”、“考公”、“国企央企招聘”等。
    5. 选择笔记，点击笔记封面，进入笔记详情页。 
    6. 在笔记详情页，将"笔记数据"中各项分别记录下来，包括：总曝光量、总阅读量、总互动量、总点赞量、总收藏量、总评论量。
    7. 点击"复制小红书笔记链接"，将笔记链接复制后也记录下来。
    8. 一页浏览完后可以点击翻页按钮，浏览下一页。
    9. 重复以上4-7步骤，直到页面都浏览完。
    """

    # If you would lik to add tools to your crew, you can learn more about it here:
    # https://docs.crewai.com/concepts/agents#agent-tools
    @agent
    def poem_writer(self) -> Agent:
        return Agent(
            config=self.agents_config["poem_writer"],
        )

    # To learn more about structured task outputs,
    # task dependencies, and task callbacks, check out the documentation:
    # https://docs.crewai.com/concepts/tasks#overview-of-a-task
    @task
    def write_poem(self) -> Task:
        return Task(
            config=self.tasks_config["write_poem"],
        )

    @crew
    def crew(self) -> Crew:
        """Creates the Research Crew"""
        # To learn how to add knowledge sources to your crew, check out the documentation:
        # https://docs.crewai.com/concepts/knowledge#what-is-knowledge

        return Crew(
            agents=self.agents,  # Automatically created by the @agent decorator
            tasks=self.tasks,  # Automatically created by the @task decorator
            process=Process.sequential,
            verbose=True,
        )
