import sys
import csv
import urllib2
import requests
import re
from itertools import izip
from lxml import html, etree
from bs4 import BeautifulSoup
import time
from BeautifulSoup import BeautifulSoup as bs

class Player:

	def __init__(self, name, position):
		self.name = name;
		self.position = position;
		self.minutes_count = [0.0] * 48;
		self.games_count = 0;

	def set_games_data(self, games_played, games_started, minutes_played):
		self.games_played = games_played;
		self.games_started = games_started;
		self.minutes_played = minutes_played;

	def add_minute_range(self, start_min, end_min):
		for i in range(start_min, end_min):
			if self.minutes_count[i] < self.games_count:
				self.minutes_count[i] += 1.0;

	def get_position_val(self):
		if "PG" in self.position:
			return 1;
		if "SG" in self.position:
			return 2;
		if "SF" in self.position:
			return 3;
		if "PF" in self.position:
			return 4;
		if "C" in self.position:
			return 5;

		print "Uh oh, no position for: " + self.name;
		return 0;

	'''def get_starting_percentage(self):
		return float(self.games_started) / float(self.games_played);

	def get_min_per_game(self):
		return float(self.minutes_played) / float(self.games_played);
	'''

def generate_player_dictionary(team_page_link):
	player_dict = {};
	response = urllib2.urlopen("http://www.basketball-reference.com" + team_page_link).read();
	team_page = BeautifulSoup(response, 'lxml');
	totals_table = team_page.find("table", {"id":"totals"});
	totals_rows = totals_table.find("tbody").findAll("tr");	
	roster_table = team_page.find("table", {"id":"roster"});
	roster_rows = roster_table.find("tbody").findAll("tr");

	for player_row in roster_rows:	
		cols = player_row.findAll("td");
		player_name = cols[1].find("a").text;
		if player_name == "Glenn Robinson":
			player_name = "Glenn Robinson III";
		position = cols[2].text;
		if player_name in player_dict:
			print 'Uh oh, we found a duplicate: ' + player_name +" on " + team_page_link;
		else:
			p = Player(player_name, position);
			player_dict[player_name] = p;

	for totals_row in totals_rows[0:len(totals_rows) - 1]:
		cols = totals_row.findAll("td");
		player_name = cols[1].find("a").text;
		if player_name == "Glenn Robinson":
			player_name = "Glenn Robinson III";
		p = player_dict[player_name];

		games_played = int(cols[3].find("a").text);
		games_started = int(cols[4].text);
		minutes_played = int(cols[5].text);

		p.set_games_data(games_played, games_started, minutes_played);

	return player_dict;		

width_regex = re.compile("width:([0-9]+)px;");
def process_plus_minus(plus_minus_link, table_index, num_overtimes, players):
	pm_page = html.fromstring(requests.get(plus_minus_link).content);
	total_width = int(width_regex.search(pm_page.xpath('//*[@id="page_content"]/table/tr/td/div[2]/div[2]')[0].attrib.get("style")).group(1)) - 1;
	team_table = pm_page.xpath('//*[@id="page_content"]/table/tr/td/div[2]/div[2]/div[' + str(table_index) + ']')[0];
	table_soup = BeautifulSoup(etree.tostring(team_table), 'lxml').find('div');
	rows = table_soup.findAll('div', recursive=False)[2:];

	total_minutes = 48.0 + (5.0 * num_overtimes);
	minute_width = total_width / total_minutes;
	for player_row, minutes_row in izip(*[iter(rows)] * 2):
		player_name = player_row.find('span').text;
		if player_name == "Jose Barea":
			player_name = "J.J. Barea";
		elif player_name == "John Lucas":
			player_name = "John Lucas III";
		elif player_name == "Glenn Robinson":
			player_name = "Glenn Robinson III";
		player_obj = players[player_name];
		player_obj.games_count += 1;
		curr_minute = 0.0;
		for bar in minutes_row.findAll('div'):
			if round(curr_minute) < 48:
				classes = bar.get('class');
				width = int(width_regex.search(bar.get('style')).group(1)) + 1;
				span_length = width / minute_width;

				if "background_lime" in classes or "background_red" in classes or "background_silver" in classes:
					try:
						player_obj.add_minute_range(int(round(curr_minute)), int(round(curr_minute + span_length)));
					except IndexError:
						print player_name, curr_minute, span_length
						raise;

				curr_minute += span_length;

def main():

	years = ["2016"];

	for year in years:
		print "DOING YEAR " + year;
		season_summary = html.fromstring(requests.get("http://www.basketball-reference.com/leagues/NBA_" + year + ".html").content);

		soup = bs(requests.get("http://www.basketball-reference.com/leagues/NBA_" + year + ".html").content)
		print soup

		# print soup.find_all('tbody')[0].find_all('a')
		# for i in range(1, 31):
		# 	abr_regex = re.compile("^\/teams\/(.*)\/.*\.html");
			# team_page_link = season_summary.xpath('//*[@id="team"]/tbody/tr[' + str(i) + ']/td[2]/a/@href')[0];
			# team_abr = abr_regex.search(team_page_link).group(1);

		# 	players = generate_player_dictionary(team_page_link);
		# 	schedule_link = "http://www.basketball-reference.com/teams/" + team_abr + "/" + year + "_games.html";
		# 	schedule_page = html.fromstring(requests.get(schedule_link).content);

		# 	print "Working on " + team_abr;
		# 	num_game_rows = 87;
		# 	if (year == "2013") and (team_abr == "BOS" or team_abr == "IND"):
		# 		num_game_rows -= 1;
		# 	for i in range(num_game_rows):
		# 		## Every 20 rows, there's a header row that we want to ignore
		# 		if not (i % 21 == 0):
		# 			link = schedule_page.xpath('//*[@id="teams_games"]/tbody/tr[' + str(i) + ']/td[5]/a/@href');
		# 			gameID_regex = re.compile('^/boxscores/([^.]+).html');
		# 			gameID = gameID_regex.search(link[0]).group(1);
		# 			isHomeGame = len(schedule_page.xpath('//*[@id="teams_games"]/tbody/tr[' + str(i) + ']/td[6]/text()')) == 0;
		# 			overtimeCell = schedule_page.xpath('//*[@id="teams_games"]/tbody/tr[' + str(i) + ']/td[9]/text()');
		# 			num_overtimes = 0;
		# 			if len(overtimeCell) == 1:
		# 				if overtimeCell[0] == "OT":
		# 					num_overtimes = 1;
		# 				else:
		# 					num_overtimes = int(overtimeCell[0][0]);
		# 			plus_minus_link = "http://www.basketball-reference.com/boxscores/plus-minus/" + gameID + ".html";

		# 			process_plus_minus(plus_minus_link, isHomeGame + 1, num_overtimes, players);

		# 	player_list = players.values();
		# 	players_by_starts = sorted(player_list, key=lambda p: p.games_started, reverse=True);
		# 	starters = sorted(players_by_starts[0:5], key=lambda p: p.get_position_val());
		# 	bench = sorted(players_by_starts[5:], key=lambda p: p.minutes_played, reverse=True);
			
		# 	with open("data/" + year + "/" + team_abr + ".csv", "wb") as f:
		# 		writer = csv.writer(f);
		# 		writer.writerow(["Name", "GamesPlayed", "MinutesPlayed"] + [str(x) for x in range(1,49)]);
		# 		for player in starters + bench:
		# 			writer.writerow([player.name, player.games_played, player.minutes_played] + [x / 82.0 for x in player.minutes_count] );

if __name__ == "__main__":
	start_time = time.time();
	main()
	print("--- %s seconds ---" % (time.time() - start_time))
