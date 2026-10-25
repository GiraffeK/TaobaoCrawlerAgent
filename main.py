import asyncio
import sys
from pathlib import Path
from typing import Optional

# Add src to python path for direct execution
sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))

import typer
from rich.console import Console
from rich.table import Table

from taobao_crawler_agent import __version__
from taobao_crawler_agent.agent import TaobaoAgent
from taobao_crawler_agent.crawler.browser import BrowserManager
from taobao_crawler_agent.storage.exporter import DataExporter

app = typer.Typer(help="TaobaoCrawlerAgent - Intelligent multi-page search, anti-bait & real SKU price crawler")
console = Console()


@app.command()
def version():
    """Show the version of TaobaoCrawlerAgent."""
    console.print(f"[bold cyan]TaobaoCrawlerAgent[/bold cyan] v{__version__}")


@app.command()
def login():
    """Open a visible browser window for you to scan QR code / log in to Taobao to save session."""
    async def _login():
        console.print("[bold yellow]Opening Taobao in interactive mode...[/bold yellow]")
        console.print("[dim]Please complete QR code or SMS login in the opened browser window.[/dim]")
        bm = BrowserManager(headless=False)
        page = await bm.new_page()
        await page.goto("https://login.taobao.com")
        console.print("[green]Waiting for login. Close the browser window or press Enter here when done.[/green]")
        try:
            await page.wait_for_url("https://www.taobao.com/**", timeout=120000)
            console.print("[bold green]Login detected successfully! Session saved in data/sessions.[/bold green]")
        except Exception:
            console.print("[yellow]Timeout or manual close. Session cookies are saved in data/sessions.[/yellow]")
        finally:
            await asyncio.sleep(2)
            await bm.close()

    asyncio.run(_login())


@app.command()
def search(
    keyword: str = typer.Argument(..., help="Search keyword or product description"),
    pages: int = typer.Option(1, "--pages", "-p", help="Number of search result pages to crawl (1~17)"),
    headless: bool = typer.Option(True, "--headless/--no-headless", help="Run browser in headless mode"),
    deep_sku: bool = typer.Option(False, "--deep-sku", help="Open detail pages to inspect real selected SKU prices"),
    min_price: Optional[float] = typer.Option(None, "--min-price", help="Minimum price floor (e.g. 1500) to filter fake bait accessories"),
    max_sku: int = typer.Option(10, "--max-sku", help="Max number of candidate products to deep-probe SKU for"),
    output_format: str = typer.Option("csv", "--format", "-f", help="Export format: csv or json"),
):
    """Run agent to search products on Taobao with smooth scroll, multi-page crawling and deep SKU pricing."""
    async def _search():
        console.print(f"[bold blue]Starting agent search for:[/bold blue] '{keyword}'")
        console.print(f"[dim]Pages: {pages} | Deep SKU Inspection: {deep_sku} | Min Price Floor: {min_price or 'None'}[/dim]\n")
        
        agent = TaobaoAgent(headless=headless)
        result = await agent.run_search(
            query_text=keyword,
            max_pages=pages,
            deep_sku=deep_sku,
            min_price_floor=min_price,
            max_sku_inspections=max_sku,
        )

        console.print(f"\n[bold green]Search Summary:[/bold green] {result.summary}\n")

        if result.top_recommendations:
            table = Table(title=f"Top Verified Recommendations for '{keyword}'")
            table.add_column("Title", style="cyan", no_wrap=False, max_width=35)
            table.add_column("Score", justify="center")
            table.add_column("List Price", style="dim", justify="right")
            if deep_sku:
                table.add_column("Real SKU", style="blue")
                table.add_column("Real Price", style="bold green", justify="right")
            else:
                table.add_column("Effective Price", style="bold green", justify="right")
            table.add_column("Sales", style="magenta")
            table.add_column("Shop", style="yellow")

            for item in result.top_recommendations[:25]:
                list_price_str = f"¥{item.price:.2f}"
                score_str = f"[bold green]{item.relevance_score}[/bold green]" if item.relevance_score >= 80 else (f"[yellow]{item.relevance_score}[/yellow]" if item.relevance_score >= 50 else f"[red]{item.relevance_score}[/red]")
                if deep_sku:
                    real_p_str = f"¥{item.real_price:.2f}" if item.real_price else "[dim]Unverified[/dim]"
                    real_sku_str = item.real_sku[:20] if item.real_sku else "-"
                    table.add_row(
                        item.title[:35] + ("..." if len(item.title) > 35 else ""),
                        score_str,
                        list_price_str,
                        real_sku_str,
                        real_p_str,
                        item.sales_count or "-",
                        item.shop_name or "-",
                    )
                else:
                    table.add_row(
                        item.title[:35] + ("..." if len(item.title) > 35 else ""),
                        score_str,
                        list_price_str,
                        list_price_str,
                        item.sales_count or "-",
                        item.shop_name or "-",
                    )
            console.print(table)

            exporter = DataExporter()
            filename = f"search_{keyword.replace(' ', '_')}"
            if output_format.lower() == "json":
                out = exporter.export_json(result.top_recommendations, filename)
            else:
                out = exporter.export_csv(result.top_recommendations, filename)
            console.print(f"\n[bold]Exported results to:[/bold] [underline]{out}[/underline]")

            # Also generate high-value Executive Buyer's Intelligence Report (.md)
            report_out = exporter.export_markdown_report(
                query=keyword,
                items=result.top_recommendations,
                summary=result.summary,
                price_range=result.price_range,
                filename=f"hunter_report_{keyword.replace(' ', '_')}",
            )
            console.print(f"[bold green]Generated Buyer Intelligence Report:[/bold green] [underline]{report_out}[/underline]")
        else:
            console.print("[yellow]No valid product items retrieved. If prompted, please run 'python main.py login' first.[/yellow]")

    asyncio.run(_search())


if __name__ == "__main__":
    app()
